import os
import re
import argparse
import time
import hashlib
import snowflake.connector

# Set a few global variables here
_snowchange_version = '2.1.0'
_metadata_database_name = 'METADATA'
_metadata_schema_name = 'SNOWCHANGE'
_metadata_table_name = 'CHANGE_HISTORY'


def snowchange(root_folder, snowflake_account, snowflake_region, snowflake_user, snowflake_role, snowflake_warehouse, change_history_table_override, autocommit, verbose):
  if "SNOWSQL_PWD" not in os.environ:
    raise ValueError("The SNOWSQL_PWD environment variable has not been defined")

  root_folder = os.path.abspath(root_folder)
  if not os.path.isdir(root_folder):
    raise ValueError("Invalid root folder: %s" % root_folder)

  print("snowchange version: %s" % _snowchange_version)
  print("Using root folder %s" % root_folder)

  # TODO: Is there a better way to do this without setting environment variables?
  os.environ["SNOWFLAKE_ACCOUNT"] = snowflake_account
  os.environ["SNOWFLAKE_USER"] = snowflake_user
  os.environ["SNOWFLAKE_ROLE"] = snowflake_role
  os.environ["SNOWFLAKE_WAREHOUSE"] = snowflake_warehouse
  os.environ["SNOWFLAKE_REGION"] = snowflake_region
  os.environ["SNOWFLAKE_AUTHENTICATOR"] = 'snowflake'

  scripts_skipped = 0
  scripts_applied = 0

  # Get the change history table details
  change_history_table = get_change_history_table_details(change_history_table_override)
 
  # Create the change history table (and containing objects) if it don't exist.
  create_change_history_table_if_missing(change_history_table, autocommit, verbose)
  print("Using change history table %s.%s.%s" % (change_history_table['database_name'], change_history_table['schema_name'], change_history_table['table_name']))

  # Find the max published version
  # TODO: Figure out how to directly SELECT the max value from Snowflake with a SQL version of the sorted_alphanumeric() logic
  max_published_version = ''
  change_history = fetch_change_history(change_history_table, autocommit, verbose)
  if change_history:
    change_history_sorted = sorted_alphanumeric(change_history)
    max_published_version = change_history_sorted[-1]
  max_published_version_display = max_published_version
  if max_published_version_display == '':
    max_published_version_display = 'None'
  print("Max applied change script version: %s" % max_published_version_display)
  if verbose:
    print("Change history: %s" % change_history)

  # Find all scripts in the root folder (recursively) and sort them correctly
  all_scripts = get_all_scripts_recursively(root_folder, verbose)
  all_script_names = list(all_scripts.keys())
  all_script_names_sorted = sorted_alphanumeric(all_script_names)

  # Loop through each script in order and apply any required changes
  for script_name in all_script_names_sorted:
    script = all_scripts[script_name]

    # Only apply a change script if the version is newer than the most recent change in the database
    if get_alphanum_key(script['script_version']) <= get_alphanum_key(max_published_version):
      if verbose:
        print("Skipping change script %s because it's older than the most recently applied change (%s)" % (script['script_name'], max_published_version))
      scripts_skipped += 1
      continue

    print("Applying change script %s" % script['script_name'])
    apply_change_script(script, change_history_table, autocommit, verbose)
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
      script_name_parts = re.search(r'^([V])(.+)__(.+)\.sql$', file_name.strip())

      # Only process valid change scripts
      if script_name_parts is None:
        if verbose:
          print("Ignoring non-change file " + file_full_path)
        continue

      # Add this script to our dictionary (as nested dictionary)
      script = dict()
      script['script_name'] = file_name
      script['script_full_path'] = file_full_path
      script['script_type'] = script_name_parts.group(1)
      script['script_version'] = script_name_parts.group(2)
      script['script_description'] = script_name_parts.group(3).replace('_', ' ').capitalize()
      all_files[file_name] = script

      # Throw an error if the same version exists more than once
      if script['script_version'] in all_versions:
        raise ValueError("The script version %s exists more than once (second instance %s)" % (script['script_version'], script['script_full_path']))
      all_versions.append(script['script_version'])

  return all_files

def execute_snowflake_query(snowflake_database, query, autocommit, verbose):
  con = snowflake.connector.connect(
    user = os.environ["SNOWFLAKE_USER"],
    account = os.environ["SNOWFLAKE_ACCOUNT"],
    role = os.environ["SNOWFLAKE_ROLE"],
    warehouse = os.environ["SNOWFLAKE_WAREHOUSE"],
    database = snowflake_database,
    region = os.environ["SNOWFLAKE_REGION"],
    authenticator = os.environ["SNOWFLAKE_AUTHENTICATOR"],
    password = os.environ["SNOWSQL_PWD"]
  )
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

def create_change_history_table_if_missing(change_history_table, autocommit, verbose):
  # Create the database if it doesn't exist
  query = "CREATE DATABASE IF NOT EXISTS {0}".format(change_history_table['database_name'])
  execute_snowflake_query('', query, autocommit, verbose)

  # Create the schema if it doesn't exist
  query = "CREATE SCHEMA IF NOT EXISTS {0}".format(change_history_table['schema_name'])
  execute_snowflake_query(change_history_table['database_name'], query, autocommit, verbose)

  # Finally, create the change history table if it doesn't exist
  query = "CREATE TABLE IF NOT EXISTS {0}.{1} (VERSION VARCHAR, DESCRIPTION VARCHAR, SCRIPT VARCHAR, SCRIPT_TYPE VARCHAR, CHECKSUM VARCHAR, EXECUTION_TIME NUMBER, STATUS VARCHAR, INSTALLED_BY VARCHAR, INSTALLED_ON TIMESTAMP_LTZ)".format(change_history_table['schema_name'], change_history_table['table_name'])
  execute_snowflake_query(change_history_table['database_name'], query, autocommit, verbose)

def fetch_change_history(change_history_table, autocommit, verbose):
  query = 'SELECT VERSION FROM {0}.{1}'.format(change_history_table['schema_name'], change_history_table['table_name'])
  results = execute_snowflake_query(change_history_table['database_name'], query, autocommit, verbose)

  # Collect all the results into a list
  change_history = list()
  for cursor in results:
    for row in cursor:
      change_history.append(row[0])

  return change_history

def apply_change_script(script, change_history_table, autocommit, verbose):
  # First read the contents of the script
  with open(script['script_full_path'],'r') as content_file:
    content = content_file.read().strip()
    content = content[:-1] if content.endswith(';') else content

  # Define a few other change related variables
  checksum = hashlib.sha224(content.encode('utf-8')).hexdigest()
  execution_time = 0
  status = 'Success'

  # Execute the contents of the script
  if len(content) > 0:
    start = time.time()
    execute_snowflake_query('', content, autocommit, verbose)
    end = time.time()
    execution_time = round(end - start)

  # Finally record this change in the change history table
  query = "INSERT INTO {0}.{1} (VERSION, DESCRIPTION, SCRIPT, SCRIPT_TYPE, CHECKSUM, EXECUTION_TIME, STATUS, INSTALLED_BY, INSTALLED_ON) values ('{2}','{3}','{4}','{5}','{6}',{7},'{8}','{9}',CURRENT_TIMESTAMP);".format(change_history_table['schema_name'], change_history_table['table_name'], script['script_version'], script['script_description'], script['script_name'], script['script_type'], checksum, execution_time, status, os.environ["SNOWFLAKE_USER"])
  execute_snowflake_query(change_history_table['database_name'], query, autocommit, verbose)


if __name__ == '__main__':
  parser = argparse.ArgumentParser(prog = 'python snowchange.py', description = 'Apply schema changes to a Snowflake account. Full readme at https://github.com/jamesweakley/snowchange', formatter_class = argparse.RawTextHelpFormatter)
  parser.add_argument('-f','--root-folder', type = str, default = ".", help = 'The root folder for the database change scripts')
  parser.add_argument('-a', '--snowflake-account', type = str, help = 'The name of the snowflake account (e.g. ly12345)', required = True)
  parser.add_argument('--snowflake-region', type = str, help = 'The name of the snowflake region (e.g. ap-southeast-2)', required = True)
  parser.add_argument('-u', '--snowflake-user', type = str, help = 'The name of the snowflake user (e.g. DEPLOYER)', required = True)
  parser.add_argument('-r', '--snowflake-role', type = str, help = 'The name of the role to use (e.g. DEPLOYER_ROLE)', required = True)
  parser.add_argument('-w', '--snowflake-warehouse', type = str, help = 'The name of the warehouse to use (e.g. DEPLOYER_WAREHOUSE)', required = True)
  parser.add_argument('-c', '--change-history-table', type = str, help = 'Used to override the default name of the change history table (e.g. METADATA.SNOWCHANGE.CHANGE_HISTORY)', required = False)
  parser.add_argument('-ac', '--autocommit', action='store_true')
  parser.add_argument('-v','--verbose', action='store_true')
  args = parser.parse_args()

  snowchange(args.root_folder, args.snowflake_account, args.snowflake_region, args.snowflake_user, args.snowflake_role, args.snowflake_warehouse, args.change_history_table, args.autocommit, args.verbose)
  