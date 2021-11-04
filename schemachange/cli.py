import os
import string
import re
import argparse
import jinja2
import json
import time
import hashlib
from jinja2.loaders import BaseLoader
import snowflake.connector
import sys
import warnings
import yaml
from typing import Dict, Any
from pandas import DataFrame
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric import dsa
from cryptography.hazmat.primitives import serialization
import io
from traceback import print_exc

# Set a few global variables here
_schemachange_version = '3.2.0'
_config_file_name = 'schemachange-config.yml'
_metadata_database_name = 'METADATA'
_metadata_schema_name = 'SCHEMACHANGE'
_metadata_table_name = 'CHANGE_HISTORY'
_snowflake_application_name = 'schemachange'

class JinjaTemplateProcessor:
  def __init__(self, project_root: str, modules_folder: str = None):
    loader: BaseLoader
    if modules_folder:
      loader =  jinja2.ChoiceLoader(
        [
          jinja2.FileSystemLoader(project_root),
          jinja2.PrefixLoader({"modules": jinja2.FileSystemLoader(modules_folder)}),
        ]
      )
    else:
      loader = jinja2.FileSystemLoader(project_root)

    self.__environment = jinja2.Environment(loader=loader, undefined=jinja2.StrictUndefined)
    self.__project_root = project_root

  def override_loader(self, loader: jinja2.BaseLoader):
    # to make unit testing easier
    self.__environment = jinja2.Environment(loader=loader, undefined=jinja2.StrictUndefined)

  def render(self, script: str, vars: Dict[str, Any], verbose: bool) -> str:
    if not vars:
      vars = {}

    template = self.__environment.get_template(script)
    content = template.render(**vars).strip()
    content = content[:-1] if content.endswith(';') else content

    return content

  def relpath(self, file_path: str):
    return os.path.relpath(file_path, self.__project_root)


def deploy_command(config):
  # Make sure we have the required configs
  if not config['snowflake-account'] or not config['snowflake-user'] or not config['snowflake-role'] or not config['snowflake-warehouse']:
    raise ValueError("Missing config values. The following config values are required: snowflake-account, snowflake-user, snowflake-role, snowflake-warehouse")

  # Password authentication will take priority
  if "SNOWFLAKE_PASSWORD" not in os.environ and "SNOWSQL_PWD" not in os.environ:  # We will accept SNOWSQL_PWD for now, but it is deprecated
    if "SNOWFLAKE_PRIVATE_KEY_PATH" not in os.environ:
      raise ValueError("Missing environment variable(s). SNOWFLAKE_PASSWORD must be defined for password authentication. SNOWFLAKE_PRIVATE_KEY_PATH and (optional) SNOWFLAKE_PRIVATE_KEY_PASSPHRASE must be defined for private key authentication.")

  # Log some additional details
  if config['dry-run']:
    print("Running in dry-run mode")
  print("Using Snowflake account %s" % config['snowflake-account'])
  print("Using default role %s" % config['snowflake-role'])
  print("Using default warehouse %s" % config['snowflake-warehouse'])
  print("Using default database %s" % config['snowflake-database'])

  # Set default Snowflake session parameters
  snowflake_session_parameters = {
    "QUERY_TAG": "schemachange %s" % _schemachange_version
  }

  # TODO: Is there a better way to do this without setting environment variables?
  os.environ["SNOWFLAKE_ACCOUNT"] = config['snowflake-account']
  os.environ["SNOWFLAKE_USER"] = config['snowflake-user']
  os.environ["SNOWFLAKE_ROLE"] = config['snowflake-role']
  os.environ["SNOWFLAKE_WAREHOUSE"] = config['snowflake-warehouse']
  os.environ["SNOWFLAKE_AUTHENTICATOR"] = 'snowflake'

  scripts_skipped = 0
  scripts_applied = 0

  # Deal with the change history table (create if specified)
  change_history_table = get_change_history_table_details(config['change-history-table'])
  change_history_metadata = fetch_change_history_metadata(change_history_table, snowflake_session_parameters, config['autocommit'], config['verbose'])
  if change_history_metadata:
    print("Using change history table %s.%s.%s (last altered %s)" % (change_history_table['database_name'], change_history_table['schema_name'], change_history_table['table_name'], change_history_metadata['last_altered']))
  elif config['create-change-history-table']:
    # Create the change history table (and containing objects) if it don't exist.
    if not config['dry-run']:
      create_change_history_table_if_missing(change_history_table, snowflake_session_parameters, config['autocommit'], config['verbose'])
    print("Created change history table %s.%s.%s" % (change_history_table['database_name'], change_history_table['schema_name'], change_history_table['table_name']))
  else:
    raise ValueError("Unable to find change history table %s.%s.%s" % (change_history_table['database_name'], change_history_table['schema_name'], change_history_table['table_name']))

  # Find the max published version
  max_published_version = ''

  change_history = None
  r_scripts_checksum = None
  if (config['dry-run'] and change_history_metadata) or not config['dry-run']:
    change_history = fetch_change_history(change_history_table, snowflake_session_parameters, config['autocommit'], config['verbose'])
    r_scripts_checksum = fetch_r_scripts_checksum(change_history_table, snowflake_session_parameters, config['autocommit'], config['verbose'])

  if change_history:
    max_published_version = change_history[0]
  max_published_version_display = max_published_version
  if max_published_version_display == '':
    max_published_version_display = 'None'
  print("Max applied change script version: %s" % max_published_version_display)

  # Find all scripts in the root folder (recursively) and sort them correctly
  all_scripts = get_all_scripts_recursively(config['root-folder'], config['verbose'])
  all_script_names = list(all_scripts.keys())
  # Sort scripts such that versioned scripts get applied first and then the repeatable ones.
  all_script_names_sorted =   sorted_alphanumeric([script for script in all_script_names if script[0] == 'V']) \
                            + sorted_alphanumeric([script for script in all_script_names if script[0] == 'R']) \
                            + sorted_alphanumeric([script for script in all_script_names if script[0] == 'A'])

  # Loop through each script in order and apply any required changes
  for script_name in all_script_names_sorted:
    script = all_scripts[script_name]

    # Apply a versioned-change script only if the version is newer than the most recent change in the database
    # Apply any other scripts, i.e. repeatable scripts, irrespective of the most recent change in the database
    if script_name[0] == 'V' and get_alphanum_key(script['script_version']) <= get_alphanum_key(max_published_version):
      if config['verbose']:
        print("Skipping change script %s because it's older than the most recently applied change (%s)" % (script['script_name'], max_published_version))
      scripts_skipped += 1
      continue

    # Always process with jinja engine
    jinja_processor = JinjaTemplateProcessor(project_root = config['root-folder'], modules_folder = config['modules-folder'])
    content = jinja_processor.render(jinja_processor.relpath(script['script_full_path']), config['vars'], config['verbose'])

    # Apply only R scripts where the checksum changed compared to the last execution of snowchange
    if script_name[0] == 'R':
      # Compute the checksum for the script
      checksum_current = hashlib.sha224(content.encode('utf-8')).hexdigest()

      # check if R file was already executed
      if (r_scripts_checksum is not None) and script_name in list(r_scripts_checksum['script_name']):
        checksum_last = list(r_scripts_checksum.loc[r_scripts_checksum['script_name'] == script_name, 'checksum'])[0]
      else:
        checksum_last = ''

      # check if there is a change of the checksum in the script
      if checksum_current == checksum_last:
        if config['verbose']:
          print(f"Skipping change script {script_name} because there is no change since the last execution")
        scripts_skipped += 1
        continue

    if config['explain-first']:
      explain_change_script(script, content, config['vars'], config['snowflake-database'], snowflake_session_parameters, config['verbose'])

    print("Applying change script %s" % script['script_name'])
    if not config['dry-run']:
      apply_change_script(script, content, config['vars'], config['snowflake-database'], change_history_table, snowflake_session_parameters, config['autocommit'], config['verbose'])

    scripts_applied += 1

  print("Successfully applied %d change scripts (skipping %d)" % (scripts_applied, scripts_skipped))
  print("Completed successfully")

def render_command(config, script_path):
  # Valide the script file path
  script_path = os.path.abspath(script_path)
  if not os.path.isfile(script_path):
    raise ValueError("Invalid script_path: %s" % script_path)

  # Always process with jinja engine
  jinja_processor = JinjaTemplateProcessor(project_root = config['root-folder'], modules_folder = config['modules-folder'])
  content = jinja_processor.render(jinja_processor.relpath(script_path), config['vars'], config['verbose'])

  checksum = hashlib.sha224(content.encode('utf-8')).hexdigest()
  print("Checksum %s" % checksum)
  print(content)


# This function will return a list containing the parts of the key (split by number parts)
# Each number is converted to and integer and string parts are left as strings
# This will enable correct sorting in python when the lists are compared
# e.g. get_alphanum_key('1.2.2') results in ['', 1, '.', 2, '.', 2, '']
def get_alphanum_key(key):
  convert = lambda text: int(text) if text.isdigit() else text.lower()
  alphanum_key = [ convert(c) for c in re.split('([0-9]+)', key) ]
  return alphanum_key

def sorted_alphanumeric(data):
  return sorted(data, key=get_alphanum_key)

def get_schemachange_config(config_file_path, root_folder, modules_folder, snowflake_account, snowflake_user, snowflake_role, snowflake_warehouse, snowflake_database, change_history_table_override, vars, create_change_history_table, autocommit, verbose, dry_run, explain_first):
  config = dict()

  # First read in the yaml config file, if present
  if os.path.isfile(config_file_path):
    with open(config_file_path) as config_file:
      # The FullLoader parameter handles the conversion from YAML scalar values to Python the dictionary format
      config = yaml.load(config_file, Loader=yaml.FullLoader)
    print("Using config file: %s" % config_file_path)

  # First the folder paths
  if root_folder:
    config['root-folder'] = root_folder
  if 'root-folder' in config:
    config['root-folder'] = os.path.abspath(config['root-folder'])
  else:
    config['root-folder'] = os.path.abspath('.')
  if not os.path.isdir(config['root-folder']):
    raise ValueError("Invalid root folder: %s" % config['root-folder'])

  if modules_folder:
    config['modules-folder'] = modules_folder
  if 'modules-folder' not in config:
    config['modules-folder'] = None
  if config['modules-folder']:
    config['modules-folder'] = os.path.abspath(config['modules-folder'])
    if not os.path.isdir(config['modules-folder']):
      raise ValueError("Invalid modules folder: %s" % config['modules-folder'])

  # Then the remaining configs
  if snowflake_account:
    config['snowflake-account'] = snowflake_account
  if 'snowflake-account' not in config:
    config['snowflake-account'] = None

  if snowflake_user:
    config['snowflake-user'] = snowflake_user
  if 'snowflake-user' not in config:
    config['snowflake-user'] = None

  if snowflake_role:
    config['snowflake-role'] = snowflake_role
  if 'snowflake-role' not in config:
    config['snowflake-role'] = None

  if snowflake_warehouse:
    config['snowflake-warehouse'] = snowflake_warehouse
  if 'snowflake-warehouse' not in config:
    config['snowflake-warehouse'] = None

  if snowflake_database:
    config['snowflake-database'] = snowflake_database
  if 'snowflake-database' not in config:
    config['snowflake-database'] = None

  if change_history_table_override:
    config['change-history-table'] = change_history_table_override
  if 'change-history-table' not in config:
    config['change-history-table'] = None

  if vars:
    config['vars'] = vars
  if 'vars' not in config:
    config['vars'] = {}

  if create_change_history_table:
    config['create-change-history-table'] = create_change_history_table
  if 'create-change-history-table' not in config:
    config['create-change-history-table'] = False

  if autocommit:
    config['autocommit'] = autocommit
  if 'autocommit' not in config:
    config['autocommit'] = False

  if verbose:
    config['verbose'] = verbose
  if 'verbose' not in config:
    config['verbose'] = False

  if dry_run:
    config['dry-run'] = dry_run
  if 'dry-run' not in config:
    config['dry-run'] = False

  if config['vars']:
    # if vars is configured wrong in the config file it will come through as a string
    if type(config['vars']) is not dict:
      raise ValueError("vars did not parse correctly, please check its configuration")

    # the variable schema change has been reserved
    if "schemachange" in config['vars']:
      raise ValueError("The variable schemachange has been reserved for use by schemachange, please use a different name")

  if explain_first:
    config['explain-first'] = explain_first
  if 'explain-first' not in config:
    config['explain-first'] = False

  return config

def get_all_scripts_recursively(root_directory, verbose):
  all_files = dict()
  all_versions = list()
  # Walk the entire directory structure recursively
  for (directory_path, directory_names, file_names) in os.walk(root_directory):
    for file_name in file_names:

      file_full_path = os.path.join(directory_path, file_name)
      script_name_parts = re.search(r'^([V])(.+?)__(.+?)\.(?:sql|sql.jinja)$', file_name.strip(), re.IGNORECASE)
      repeatable_script_name_parts = re.search(r'^([R])__(.+?)\.(?:sql|sql.jinja)$', file_name.strip(), re.IGNORECASE)
      always_script_name_parts = re.search(r'^([A])__(.+?)\.(?:sql|sql.jinja)$', file_name.strip(), re.IGNORECASE)

      # Set script type depending on whether it matches the versioned file naming format
      if script_name_parts is not None:
        script_type = 'V'
        if verbose:
          print("Found Versioned file " + file_full_path)
      elif repeatable_script_name_parts is not None:
        script_type = 'R'
        if verbose:
          print("Found Repeatable file " + file_full_path)
      elif always_script_name_parts is not None:
        script_type = 'A'
        if verbose:
          print("Found Always file " + file_full_path)
      else:
        if verbose:
          print("Ignoring non-change file " + file_full_path)
        continue

      # script name is the filename without any jinja extension
      (file_part, extension_part) = os.path.splitext(file_name)
      if extension_part.upper() == ".JINJA":
        script_name = file_part
      else:
        script_name = file_name

      # Add this script to our dictionary (as nested dictionary)
      script = dict()
      script['script_name'] = script_name
      script['script_full_path'] = file_full_path
      script['script_type'] = script_type
      script['script_version'] = '' if script_type in ['R', 'A'] else script_name_parts.group(2)
      if script_type == 'R':
        script['script_description'] = repeatable_script_name_parts.group(2).replace('_', ' ').capitalize()
      elif script_type == 'A':
        script['script_description'] = always_script_name_parts.group(2).replace('_', ' ').capitalize()
      else:
        script['script_description'] = script_name_parts.group(3).replace('_', ' ').capitalize()

      # Throw an error if the script_name already exists
      if script_name in all_files:
        raise ValueError("The script name %s exists more than once (first_instance %s, second instance %s)" % (script_name, all_files[script_name]['script_full_path'], script['script_full_path']))

      all_files[script_name] = script

      # Throw an error if the same version exists more than once
      if script_type == 'V':
        if script['script_version'] in all_versions:
          raise ValueError("The script version %s exists more than once (second instance %s)" % (script['script_version'], script['script_full_path']))
        all_versions.append(script['script_version'])

  return all_files

def execute_snowflake_query(snowflake_database, query, snowflake_session_parameters, autocommit, verbose):
  # Password authentication is the default
  snowflake_password = None
  if os.getenv("SNOWFLAKE_PASSWORD") is not None and os.getenv("SNOWFLAKE_PASSWORD"):
    snowflake_password = os.getenv("SNOWFLAKE_PASSWORD")
  elif os.getenv("SNOWSQL_PWD") is not None and os.getenv("SNOWSQL_PWD"):  # Check legacy/deprecated env variable
    snowflake_password = os.getenv("SNOWSQL_PWD")
    warnings.warn("The SNOWSQL_PWD environment variable is deprecated and will be removed in a later version of schemachange. Please use SNOWFLAKE_PASSWORD instead.", DeprecationWarning)

  if snowflake_password is not None:
    if verbose:
      print("Proceeding with password authentication")

    con = snowflake.connector.connect(
      user = os.environ["SNOWFLAKE_USER"],
      account = os.environ["SNOWFLAKE_ACCOUNT"],
      role = os.environ["SNOWFLAKE_ROLE"],
      warehouse = os.environ["SNOWFLAKE_WAREHOUSE"],
      database = snowflake_database,
      authenticator = os.environ["SNOWFLAKE_AUTHENTICATOR"],
      password = snowflake_password,
      application = _snowflake_application_name,
      session_parameters = snowflake_session_parameters
    )
  # If no password, try private key authentication
  elif os.getenv("SNOWFLAKE_PRIVATE_KEY_PATH", ''):
    if verbose:
      print("Proceeding with private key authentication")

    private_key_password = os.getenv("SNOWFLAKE_PRIVATE_KEY_PASSPHRASE", '')
    if private_key_password:
      private_key_password = private_key_password.encode()
    else:
      private_key_password = None
      if verbose:
        print("No private key passphrase provided. Assuming the key is not encrypted.")
    with open(os.environ["SNOWFLAKE_PRIVATE_KEY_PATH"], "rb") as key:
      p_key= serialization.load_pem_private_key(
          key.read(),
          password = private_key_password,
          backend = default_backend()
      )

    pkb = p_key.private_bytes(
        encoding = serialization.Encoding.DER,
        format = serialization.PrivateFormat.PKCS8,
        encryption_algorithm = serialization.NoEncryption())

    con = snowflake.connector.connect(
      user = os.environ["SNOWFLAKE_USER"],
      account = os.environ["SNOWFLAKE_ACCOUNT"],
      role = os.environ["SNOWFLAKE_ROLE"],
      warehouse = os.environ["SNOWFLAKE_WAREHOUSE"],
      database = snowflake_database,
      authenticator = os.environ["SNOWFLAKE_AUTHENTICATOR"],
      application = _snowflake_application_name,
      private_key = pkb,
      session_parameters = snowflake_session_parameters
    )
  else:
    raise ValueError("Unable to find connection credentials for private key or password authentication")

  if not autocommit:
    con.autocommit(False)

  if verbose:
      print("SQL query: %s" % query)

  try:
    res = con.execute_string(query)
    if not autocommit:
      con.commit()
    return res
  except Exception as e:
    if not autocommit:
      con.rollback()
    raise e
  finally:
    con.close()

def get_change_history_table_details(change_history_table_override):
  # Start with the global defaults
  details = dict()
  details['database_name'] = _metadata_database_name.upper()
  details['schema_name'] = _metadata_schema_name.upper()
  details['table_name'] = _metadata_table_name.upper()

  # Then override the defaults if requested. The name could be in one, two or three part notation.
  if change_history_table_override is not None:
    table_name_parts = change_history_table_override.strip().split('.')

    if len(table_name_parts) == 1:
      details['table_name'] = table_name_parts[0].upper()
    elif len(table_name_parts) == 2:
      details['table_name'] = table_name_parts[1].upper()
      details['schema_name'] = table_name_parts[0].upper()
    elif len(table_name_parts) == 3:
      details['table_name'] = table_name_parts[2].upper()
      details['schema_name'] = table_name_parts[1].upper()
      details['database_name'] = table_name_parts[0].upper()
    else:
      raise ValueError("Invalid change history table name: %s" % change_history_table_override)

  return details

def fetch_change_history_metadata(change_history_table, snowflake_session_parameters, autocommit, verbose):
  # This should only ever return 0 or 1 rows
  query = "SELECT CREATED, LAST_ALTERED FROM {0}.INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA ILIKE '{1}' AND TABLE_NAME ILIKE '{2}'".format(change_history_table['database_name'], change_history_table['schema_name'], change_history_table['table_name'])
  results = execute_snowflake_query(change_history_table['database_name'], query, snowflake_session_parameters, autocommit, verbose)

  # Collect all the results into a list
  change_history_metadata = dict()
  for cursor in results:
    for row in cursor:
      change_history_metadata['created'] = row[0]
      change_history_metadata['last_altered'] = row[1]

  return change_history_metadata

def create_change_history_table_if_missing(change_history_table, snowflake_session_parameters, autocommit, verbose):
  # Check if schema exists
  query = "SELECT COUNT(1) FROM {0}.INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME ILIKE '{1}'".format(change_history_table['database_name'], change_history_table['schema_name'])
  results = execute_snowflake_query(change_history_table['database_name'], query, snowflake_session_parameters, autocommit, verbose)
  schema_exists = False
  for cursor in results:
    for row in cursor:
      schema_exists = (row[0] > 0)

  # Create the schema if it doesn't exist
  if not schema_exists:
    query = "CREATE SCHEMA {0}".format(change_history_table['schema_name'])
    execute_snowflake_query(change_history_table['database_name'], query, snowflake_session_parameters, autocommit, verbose)

  # Finally, create the change history table if it doesn't exist
  query = "CREATE TABLE IF NOT EXISTS {0}.{1} (VERSION VARCHAR, DESCRIPTION VARCHAR, SCRIPT VARCHAR, SCRIPT_TYPE VARCHAR, CHECKSUM VARCHAR, EXECUTION_TIME NUMBER, STATUS VARCHAR, INSTALLED_BY VARCHAR, INSTALLED_ON TIMESTAMP_LTZ)".format(change_history_table['schema_name'], change_history_table['table_name'])
  execute_snowflake_query(change_history_table['database_name'], query, snowflake_session_parameters, autocommit, verbose)

def fetch_r_scripts_checksum(change_history_table, snowflake_session_parameters, autocommit, verbose):
  query = f"SELECT DISTINCT SCRIPT, FIRST_VALUE(CHECKSUM) OVER (PARTITION BY SCRIPT ORDER BY INSTALLED_ON DESC) \
          FROM {change_history_table['schema_name']}.{change_history_table['table_name']} \
          WHERE SCRIPT_TYPE = 'R' AND STATUS = 'Success'"
  results = execute_snowflake_query(change_history_table['database_name'], query, snowflake_session_parameters, autocommit, verbose)

  # Collect all the results into a dict
  d_script_checksum = DataFrame(columns=['script_name', 'checksum'])
  script_names = []
  checksums = []
  for cursor in results:
    for row in cursor:
      script_names.append(row[0])
      checksums.append(row[1])

  d_script_checksum['script_name'] = script_names
  d_script_checksum['checksum'] = checksums
  return d_script_checksum

def fetch_change_history(change_history_table, snowflake_session_parameters, autocommit, verbose):
  query = "SELECT VERSION FROM {0}.{1} WHERE SCRIPT_TYPE = 'V' ORDER BY INSTALLED_ON DESC LIMIT 1".format(change_history_table['schema_name'], change_history_table['table_name'])
  results = execute_snowflake_query(change_history_table['database_name'], query, snowflake_session_parameters, autocommit, verbose)

  # Collect all the results into a list
  change_history = list()
  for cursor in results:
    for row in cursor:
      change_history.append(row[0])

  return change_history

def apply_change_script(script, script_content, vars, default_database, change_history_table, snowflake_session_parameters, autocommit, verbose):
  # Define a few other change related variables
  checksum = hashlib.sha224(script_content.encode('utf-8')).hexdigest()
  execution_time = 0
  status = 'Success'

  # Execute the contents of the script
  if len(script_content) > 0:
    start = time.time()
    session_parameters = snowflake_session_parameters.copy()
    session_parameters["QUERY_TAG"] += ";%s" % script['script_name']
    execute_snowflake_query(default_database, script_content, session_parameters, autocommit, verbose)
    end = time.time()
    execution_time = round(end - start)

  # Finally record this change in the change history table
  query = "INSERT INTO {0}.{1} (VERSION, DESCRIPTION, SCRIPT, SCRIPT_TYPE, CHECKSUM, EXECUTION_TIME, STATUS, INSTALLED_BY, INSTALLED_ON) values ('{2}','{3}','{4}','{5}','{6}',{7},'{8}','{9}',CURRENT_TIMESTAMP);".format(change_history_table['schema_name'], change_history_table['table_name'], script['script_version'], script['script_description'], script['script_name'], script['script_type'], checksum, execution_time, status, os.environ["SNOWFLAKE_USER"])
  execute_snowflake_query(change_history_table['database_name'], query, snowflake_session_parameters, autocommit, verbose)


def explain_change_script(script, content, vars, default_database, snowflake_session_parameters, verbose):
  '''
  Run "explain <statement>" for every <statement> in a script of <statement>; <statement>; ...
  This will throw an error if the explain fails, which will catch many issues with the script without needing to directly execute it.
  '''

  content_io = io.StringIO(content)
  statements = snowflake.connector.util_text.split_statements(content_io)
  for n, (s, _) in enumerate(statements):
      print(f'Explaining statement {n}...')
      explain = f"explain {s}"
      try:
        execute_snowflake_query(default_database, explain, snowflake_session_parameters, False, verbose)
      except:
        if n == 0:
          raise
        else:
          warnings.warn(f'Statement {n} failed, but allowing failures for n > 0.')
          print_exc()


def main():
  parser = argparse.ArgumentParser(prog = 'schemachange', description = 'Apply schema changes to a Snowflake account. Full readme at https://github.com/Snowflake-Labs/schemachange', formatter_class = argparse.RawTextHelpFormatter)
  subcommands = parser.add_subparsers(dest='subcommand')

  parser_deploy = subcommands.add_parser("deploy")
  parser_deploy.add_argument('--config-folder', type = str, default = '.', help = 'The folder to look in for the schemachange-config.yml file (the default is the current working directory)', required = False)
  parser_deploy.add_argument('-f', '--root-folder', type = str, help = 'The root folder for the database change scripts', required = False)
  parser_deploy.add_argument('-m', '--modules-folder', type = str, help = 'The modules folder for jinja macros and templates to be used across multiple scripts', required = False)
  parser_deploy.add_argument('-a', '--snowflake-account', type = str, help = 'The name of the snowflake account (e.g. xy12345.east-us-2.azure)', required = False)
  parser_deploy.add_argument('-u', '--snowflake-user', type = str, help = 'The name of the snowflake user', required = False)
  parser_deploy.add_argument('-r', '--snowflake-role', type = str, help = 'The name of the default role to use', required = False)
  parser_deploy.add_argument('-w', '--snowflake-warehouse', type = str, help = 'The name of the default warehouse to use. Can be overridden in the change scripts.', required = False)
  parser_deploy.add_argument('-d', '--snowflake-database', type = str, help = 'The name of the default database to use. Can be overridden in the change scripts.', required = False)
  parser_deploy.add_argument('-c', '--change-history-table', type = str, help = 'Used to override the default name of the change history table (the default is METADATA.SCHEMACHANGE.CHANGE_HISTORY)', required = False)
  parser_deploy.add_argument('--vars', type = json.loads, help = 'Define values for the variables to replaced in change scripts, given in JSON format (e.g. {"variable1": "value1", "variable2": "value2"})', required = False)
  parser_deploy.add_argument('--create-change-history-table', action='store_true', help = 'Create the change history schema and table, if they do not exist (the default is False)', required = False)
  parser_deploy.add_argument('-ac', '--autocommit', action='store_true', help = 'Enable autocommit feature for DML commands (the default is False)', required = False)
  parser_deploy.add_argument('-v','--verbose', action='store_true', help = 'Display verbose debugging details during execution (the default is False)', required = False)
  parser_deploy.add_argument('--dry-run', action='store_true', help = 'Run schemachange in dry run mode (the default is False)', required = False)
  parser_deploy.add_argument('--explain-first', action='store_true', help = 'Run explain <statement> before each query is run properly, which can be used to pre-validate validate syntax etc. Works with most, but not all, Snowflake statements.')

  parser_render = subcommands.add_parser('render', description="Renders a script to the console, used to check and verify jinja output from scripts.")
  parser_render.add_argument('--config-folder', type = str, default = '.', help = 'The folder to look in for the schemachange-config.yml file (the default is the current working directory)', required = False)
  parser_render.add_argument('-f', '--root-folder', type = str, help = 'The root folder for the database change scripts', required = False)
  parser_render.add_argument('-m', '--modules-folder', type = str, help = 'The modules folder for jinja macros and templates to be used across multiple scripts', required = False)
  parser_render.add_argument('--vars', type = json.loads, help = 'Define values for the variables to replaced in change scripts, given in JSON format (e.g. {"variable1": "value1", "variable2": "value2"})', required = False)
  parser_render.add_argument('-v', '--verbose', action='store_true', help = 'Display verbose debugging details during execution (the default is False)', required = False)
  parser_render.add_argument('script', type = str, help = 'The script to render')

  # The original parameters did not support subcommands. Check if a subcommand has been supplied
  # if not default to deploy to match original behaviour.
  args = sys.argv[1:]
  if len(args) == 0 or not any(subcommand in args[0].upper() for subcommand in ["DEPLOY", "RENDER"]):
    args = ["deploy"] + args

  args = parser.parse_args(args)

  print("schemachange version: %s" % _schemachange_version)

  # First get the config values
  config_file_path = os.path.join(args.config_folder, _config_file_name)
  if args.subcommand == 'render':
    config = get_schemachange_config(config_file_path, args.root_folder, args.modules_folder, None, None, None, None, None, None, args.vars, None, None, args.verbose, None, None)
  else:
    config = get_schemachange_config(config_file_path, args.root_folder, args.modules_folder, args.snowflake_account, args.snowflake_user, args.snowflake_role, args.snowflake_warehouse, args.snowflake_database, args.change_history_table, args.vars, args.create_change_history_table, args.autocommit, args.verbose, args.dry_run, args.explain_first)

  # Then log some details
  print("Using root folder %s" % config['root-folder'])
  if config['modules-folder']:
    print("Using Jinja modules folder %s" % config['modules-folder'])
  print("Using variables %s" % config['vars'])

  # Finally, execute the command
  if args.subcommand == 'render':
    render_command(config, args.script)
  else:
    deploy_command(config)

if __name__ == "__main__":
    main()
