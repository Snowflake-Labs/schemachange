import os
import string
import re
import argparse
import json
import time
import hashlib
import snowflake.connector
import warnings
from pandas import DataFrame
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric import dsa
from cryptography.hazmat.primitives import serialization

# Set a few global variables here
_schemachange_version = '2.9.2'
_metadata_database_name = 'METADATA'
_metadata_schema_name = 'SCHEMACHANGE'
_metadata_table_name = 'CHANGE_HISTORY'

# Define the Jinja expression template class
# schemachange uses Jinja style variable references of the form "{{ variablename }}"
# See https://jinja.palletsprojects.com/en/2.11.x/templates/
# Variable names follow Python variable naming conventions
class JinjaExpressionTemplate(string.Template):
    delimiter = '{{ '
    pattern = r'''
    \{\{[ ](?:
    (?P<escaped>\{\{)|
    (?P<named>[_A-Za-z][_A-Za-z0-9]*)[ ]\}\}|
    (?P<braced>[_A-Za-z][_A-Za-z0-9]*)[ ]\}\}|
    (?P<invalid>)
    )
    '''

def schemachange(root_folder, snowflake_account, snowflake_user, snowflake_role, snowflake_warehouse, snowflake_database, change_history_table_override, vars, create_change_history_table, autocommit, verbose, dry_run):
  if dry_run:
    print("Running in dry-run mode")

  # Password authentication will take priority
  if "SNOWFLAKE_PASSWORD" not in os.environ and "SNOWSQL_PWD" not in os.environ:  # We will accept SNOWSQL_PWD for now, but it is deprecated
    if "SNOWFLAKE_PRIVATE_KEY_PATH" not in os.environ or "SNOWFLAKE_PRIVATE_KEY_PASSPHRASE" not in os.environ:
      raise ValueError("Missing environment variable(s). SNOWFLAKE_PASSWORD must be defined for password authentication. SNOWFLAKE_PRIVATE_KEY_PATH and SNOWFLAKE_PRIVATE_KEY_PASSPHRASE must be defined for private key authentication.")

  root_folder = os.path.abspath(root_folder)
  if not os.path.isdir(root_folder):
    raise ValueError("Invalid root folder: %s" % root_folder)

  print("schemachange version: %s" % _schemachange_version)
  print("Using root folder %s" % root_folder)
  print("Using variables %s" % vars)
  print("Using Snowflake account %s" % snowflake_account)
  print("Using default role %s" % snowflake_role)
  print("Using default warehouse %s" % snowflake_warehouse)
  print("Using default database %s" % snowflake_database)

  # Set default Snowflake session parameters
  snowflake_session_parameters = {
    "QUERY_TAG": "schemachange %s" % _schemachange_version
  }

  # TODO: Is there a better way to do this without setting environment variables?
  os.environ["SNOWFLAKE_ACCOUNT"] = snowflake_account
  os.environ["SNOWFLAKE_USER"] = snowflake_user
  os.environ["SNOWFLAKE_ROLE"] = snowflake_role
  os.environ["SNOWFLAKE_WAREHOUSE"] = snowflake_warehouse
  os.environ["SNOWFLAKE_AUTHENTICATOR"] = 'snowflake'

  scripts_skipped = 0
  scripts_applied = 0

  # Deal with the change history table (create if specified)
  change_history_table = get_change_history_table_details(change_history_table_override)
  change_history_metadata = fetch_change_history_metadata(change_history_table, snowflake_session_parameters, autocommit, verbose)
  if change_history_metadata:
    print("Using change history table %s.%s.%s (last altered %s)" % (change_history_table['database_name'], change_history_table['schema_name'], change_history_table['table_name'], change_history_metadata['last_altered']))
  elif create_change_history_table:
    # Create the change history table (and containing objects) if it don't exist.
    if not dry_run:
      create_change_history_table_if_missing(change_history_table, snowflake_session_parameters, autocommit, verbose)
    print("Created change history table %s.%s.%s" % (change_history_table['database_name'], change_history_table['schema_name'], change_history_table['table_name']))
  else:
    raise ValueError("Unable to find change history table %s.%s.%s" % (change_history_table['database_name'], change_history_table['schema_name'], change_history_table['table_name']))

  # Find the max published version
  max_published_version = ''

  change_history = None
  if (dry_run and change_history_metadata) or not dry_run:
    change_history = fetch_change_history(change_history_table, snowflake_session_parameters, autocommit, verbose)
    r_scripts_checksum = fetch_r_scripts_checksum(change_history_table, snowflake_session_parameters, autocommit, verbose)

  if change_history:
    max_published_version = change_history[0]
  max_published_version_display = max_published_version
  if max_published_version_display == '':
    max_published_version_display = 'None'
  print("Max applied change script version: %s" % max_published_version_display)

  # Find all scripts in the root folder (recursively) and sort them correctly
  all_scripts = get_all_scripts_recursively(root_folder, verbose)
  all_script_names = list(all_scripts.keys())
  # Sort scripts such that versioned scripts get applied first and then the repeatable ones.
  all_script_names_sorted =   sorted_alphanumeric([script for script in all_script_names if script[0] == 'V']) \
                            + sorted_alphanumeric([script for script in all_script_names if script[0] == 'R'])  

  # Loop through each script in order and apply any required changes
  for script_name in all_script_names_sorted:
    script = all_scripts[script_name]

    # Apply a versioned-change script only if the version is newer than the most recent change in the database
    # Apply any other scripts, i.e. repeatable scripts, irrespective of the most recent change in the database
    if script_name[0] == 'V' and get_alphanum_key(script['script_version']) <= get_alphanum_key(max_published_version):
      if verbose:
        print("Skipping change script %s because it's older than the most recently applied change (%s)" % (script['script_name'], max_published_version))
      scripts_skipped += 1
      continue
    
    # Apply only R scripts where the checksum changed compared to the last execution of snowchange
    if script_name[0] == 'R':
      # get checksum of current R script
      with open(script['script_full_path'],'r') as content_file:
        content = content_file.read().strip()
        content = content[:-1] if content.endswith(';') else content
        checksum_current = hashlib.sha224(content.encode('utf-8')).hexdigest()
        checksum_last = list(r_scripts_checksum.loc[r_scripts_checksum['script_name'] == script_name, 'checksum'])[0]

        # check if there is a change of the checksum in the script
        if checksum_current == checksum_last:
          if verbose:
            print(f"Skipping change script {script_name} because there is no change since the last execution")
          scripts_skipped += 1
          continue

    print("Applying change script %s" % script['script_name'])
    if not dry_run:
      apply_change_script(script, vars, snowflake_database, change_history_table, snowflake_session_parameters, autocommit, verbose)

    scripts_applied += 1

  print("Successfully applied %d change scripts (skipping %d)" % (scripts_applied, scripts_skipped))
  print("Completed successfully")

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

def get_all_scripts_recursively(root_directory, verbose):
  all_files = dict()
  all_versions = list()
  # Walk the entire directory structure recursively
  for (directory_path, directory_names, file_names) in os.walk(root_directory):
    for file_name in file_names:
      
      file_full_path = os.path.join(directory_path, file_name)
      script_name_parts = re.search(r'^([V])(.+)__(.+)\.(?:sql|SQL)$', file_name.strip())
      repeatable_script_name_parts = re.search(r'^([R])__(.+)\.(?:sql|SQL)$', file_name.strip())

      # Set script type depending on whether it matches the versioned file naming format
      if script_name_parts is not None:
        script_type = 'V'
        if verbose:
          print("Versioned file " + file_full_path)
      elif repeatable_script_name_parts is not None:
        script_type = 'R'
        if verbose:
          print("Repeatable file " + file_full_path)
      else:
        if verbose:
          print("Ignoring non-change file " + file_full_path)
        continue

      # Add this script to our dictionary (as nested dictionary)
      script = dict()
      script['script_name'] = file_name
      script['script_full_path'] = file_full_path
      script['script_type'] = script_type
      script['script_version'] = None if script_type == 'R' else script_name_parts.group(2)
      script['script_description'] = (repeatable_script_name_parts.group(2) if script_type == 'R' else script_name_parts.group(3)).replace('_', ' ').capitalize()
      all_files[file_name] = script

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
      session_parameters = snowflake_session_parameters
    )
  # If no password, try private key authentication
  elif os.getenv("SNOWFLAKE_PRIVATE_KEY_PATH") is not None and os.getenv("SNOWFLAKE_PRIVATE_KEY_PATH") and os.getenv("SNOWFLAKE_PRIVATE_KEY_PASSPHRASE") is not None and os.getenv("SNOWFLAKE_PRIVATE_KEY_PASSPHRASE"):
    if verbose:
      print("Proceeding with private key authentication")

    with open(os.environ["SNOWFLAKE_PRIVATE_KEY_PATH"], "rb") as key:
      p_key= serialization.load_pem_private_key(
          key.read(),
          password = os.environ['SNOWFLAKE_PRIVATE_KEY_PASSPHRASE'].encode(),
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
  r_script_checksums = DataFrame(columns=['script_name', 'checksum'])
  script_names = []
  checksums = []
  for cursor in results:
    for row in cursor:
      script_names.append(row[0])
      checksums.append(row[1])

  r_script_checksums['script_name'] = script_names
  r_script_checksums['checksum'] = checksums
  return r_script_checksums

def fetch_change_history(change_history_table, snowflake_session_parameters, autocommit, verbose):
  query = "SELECT VERSION FROM {0}.{1} WHERE SCRIPT_TYPE = 'V' ORDER BY INSTALLED_ON DESC LIMIT 1".format(change_history_table['schema_name'], change_history_table['table_name'])
  results = execute_snowflake_query(change_history_table['database_name'], query, snowflake_session_parameters, autocommit, verbose)

  # Collect all the results into a list
  change_history = list()
  for cursor in results:
    for row in cursor:
      change_history.append(row[0])

  return change_history

def apply_change_script(script, vars, default_database, change_history_table, snowflake_session_parameters, autocommit, verbose):
  # First read the contents of the script
  with open(script['script_full_path'],'r') as content_file:
    content = content_file.read().strip()
    content = content[:-1] if content.endswith(';') else content

  # Define a few other change related variables
  checksum = hashlib.sha224(content.encode('utf-8')).hexdigest()
  execution_time = 0
  status = 'Success'

  # Replace any variables used in the script content
  content = replace_variables_references(content, vars, verbose)

  # Execute the contents of the script
  if len(content) > 0:
    start = time.time()
    session_parameters = snowflake_session_parameters.copy()
    session_parameters["QUERY_TAG"] += ";%s" % script['script_name']
    execute_snowflake_query(default_database, content, session_parameters, autocommit, verbose)
    end = time.time()
    execution_time = round(end - start)

  # Finally record this change in the change history table
  query = "INSERT INTO {0}.{1} (VERSION, DESCRIPTION, SCRIPT, SCRIPT_TYPE, CHECKSUM, EXECUTION_TIME, STATUS, INSTALLED_BY, INSTALLED_ON) values ('{2}','{3}','{4}','{5}','{6}',{7},'{8}','{9}',CURRENT_TIMESTAMP);".format(change_history_table['schema_name'], change_history_table['table_name'], script['script_version'], script['script_description'], script['script_name'], script['script_type'], checksum, execution_time, status, os.environ["SNOWFLAKE_USER"])
  execute_snowflake_query(change_history_table['database_name'], query, snowflake_session_parameters, autocommit, verbose)

# This method will throw an error if there are any leftover variables in the change script
# Since a leftover variable in the script isn't valid SQL, and will fail when run it's
# better to throw an error here and have the user fix the problem ahead of time.
def replace_variables_references(content, vars, verbose):
  t = JinjaExpressionTemplate(content)
  return t.substitute(vars)


def main():
  parser = argparse.ArgumentParser(prog = 'schemachange', description = 'Apply schema changes to a Snowflake account. Full readme at https://github.com/Snowflake-Labs/schemachange', formatter_class = argparse.RawTextHelpFormatter)
  parser.add_argument('-f','--root-folder', type = str, default = ".", help = 'The root folder for the database change scripts', required = False)
  parser.add_argument('-a', '--snowflake-account', type = str, help = 'The name of the snowflake account (e.g. xy12345.east-us-2.azure)', required = True)
  parser.add_argument('-u', '--snowflake-user', type = str, help = 'The name of the snowflake user', required = True)
  parser.add_argument('-r', '--snowflake-role', type = str, help = 'The name of the default role to use', required = True)
  parser.add_argument('-w', '--snowflake-warehouse', type = str, help = 'The name of the default warehouse to use. Can be overridden in the change scripts.', required = True)
  parser.add_argument('-d', '--snowflake-database', type = str, help = 'The name of the default database to use. Can be overridden in the change scripts.', required = False)
  parser.add_argument('-c', '--change-history-table', type = str, help = 'Used to override the default name of the change history table (the default is METADATA.SCHEMACHANGE.CHANGE_HISTORY)', required = False)
  parser.add_argument('--vars', type = json.loads, help = 'Define values for the variables to replaced in change scripts, given in JSON format (e.g. {"variable1": "value1", "variable2": "value2"})', required = False)
  parser.add_argument('--create-change-history-table', action='store_true', help = 'Create the change history schema and table, if they do not exist (the default is False)', required = False)
  parser.add_argument('-ac', '--autocommit', action='store_true', help = 'Enable autocommit feature for DML commands (the default is False)', required = False)
  parser.add_argument('-v','--verbose', action='store_true', help = 'Display verbose debugging details during execution (the default is False)', required = False)
  parser.add_argument('--dry-run', action='store_true', help = 'Run schemachange in dry run mode (the default is False)', required = False)
  args = parser.parse_args()

  schemachange(args.root_folder, args.snowflake_account, args.snowflake_user, args.snowflake_role, args.snowflake_warehouse, args.snowflake_database, args.change_history_table, args.vars, args.create_change_history_table, args.autocommit, args.verbose, args.dry_run)

if __name__ == "__main__":
    main()
