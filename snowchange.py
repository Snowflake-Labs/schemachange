import os
import snowflake.connector
import re
import argparse


def snowchange(environment_name,snowflake_account,snowflake_user,snowflake_role,snowflake_warehouse,snowflake_region,repo_revision,root_folder,database_naming_convention,verbose):
  if os.environ["SNOWSQL_PWD"] is None:
    raise ValueError("The SNOWSQL_PWD environment variable has not been defined")
  root_folder=os.path.abspath(root_folder)
  if not os.path.isdir(root_folder):
    raise ValueError("Invalid root folder: %s" % root_folder)
  databases_folder=os.path.join(root_folder,'databases')
  if not os.path.isdir(root_folder):
    raise ValueError("Root folder does not contain a 'databases' subfolder")
  print("root_folder: %s" % root_folder)
  print("environment_name: %s" % environment_name)
  print("database_naming_convention: %s" % database_naming_convention)
  os.environ["SNOWFLAKE_ACCOUNT"]=snowflake_account
  os.environ["SNOWFLAKE_USER"]=snowflake_user
  os.environ["SNOWFLAKE_ROLE"]=snowflake_role
  os.environ["SNOWFLAKE_WAREHOUSE"]=snowflake_warehouse
  os.environ["SNOWFLAKE_REGION"] = snowflake_region
  os.environ["SNOWFLAKE_AUTHENTICATOR"]='snowflake'

  for database_folder in os.scandir(databases_folder):
    if database_folder.is_dir():
      print("Processing database %s" % database_folder.name)
      snowflake_database_name=database_naming_convention.format(database_folder.name,environment_name)
      print("snowflake database name: %s" % snowflake_database_name)
        
      create_database_if_missing(snowflake_database_name,verbose)

      for schema_folder in os.scandir(database_folder):
        schema_name=schema_folder.name
        print("Processing schema %s" % schema_name)
        create_schema_if_missing(snowflake_database_name,schema_name,verbose)
        create_schema_history_table_if_missing(snowflake_database_name,schema_name,verbose)
        schema_history=fetch_schema_history(snowflake_database_name,schema_name,verbose)
        if verbose:
            print("Schema history: %s" % schema_history)
        for schema_changeset_file in os.scandir(schema_folder):
          if re.match(r'\d{8}_\w*\.sql',schema_changeset_file.name):
            print("Processing changeset file %s" % schema_changeset_file.name)
            if schema_changeset_file.name in schema_history:
              print("Skipping changeset file %s as it has already been applied" % schema_changeset_file.name)
            else:
              print("Applying changeset file %s" % schema_changeset_file.name)
              apply_schema_file(snowflake_database_name, schema_name, schema_changeset_file, repo_revision,
                                  verbose)
          else:
            print("Skipping file %s as the name is invalid" % schema_changeset_file.name)
  print("Completed successfully")

def execute_snowflake_query(snowflake_database,snowflake_schema,query,verbose):
  con = snowflake.connector.connect(
    user=os.environ["SNOWFLAKE_USER"],
    account=os.environ["SNOWFLAKE_ACCOUNT"],
    role=os.environ["SNOWFLAKE_ROLE"],
    warehouse=os.environ["SNOWFLAKE_WAREHOUSE"],
    database=snowflake_database,
    schema=snowflake_schema,
    region=os.environ["SNOWFLAKE_REGION"],
    authenticator=os.environ["SNOWFLAKE_AUTHENTICATOR"],
    password=os.environ["SNOWSQL_PWD"]
  )
  if verbose:
      print("SQL query: %s" % query)
  try:
    return con.execute_string(query)
  finally:
    con.close()

def fetch_schema_history(snowflake_database,snowflake_schema,verbose):
  query = 'select script_name from schema_history'
  results = execute_snowflake_query(snowflake_database,snowflake_schema,query,verbose)
  schema_history=[]
  for cursor in results:
    for row in cursor:
      schema_history.append(row[0])
  return schema_history

def create_database_if_missing(database,verbose):
  query = "create database if not exists {0}".format(database)
  execute_snowflake_query('UTIL_DB',"",query,verbose)

def create_schema_if_missing(snowflake_database,schema,verbose):
  query = "create schema if not exists {0}".format(schema)
  execute_snowflake_query(snowflake_database,schema,query,verbose)

def create_schema_history_table_if_missing(snowflake_database,snowflake_schema,verbose):
  query = "create table if not exists schema_history (script_name varchar,date_deployed datetime default current_timestamp::timestamp_ntz,repo_revision varchar)"
  execute_snowflake_query(snowflake_database,snowflake_schema,query,verbose)

def apply_schema_file(snowflake_database,snowflake_schema,file,repo_revision,verbose):
  with open(file.path,'r') as content_file:
    content = content_file.read().strip()
    content = content[:-1] if content.endswith(';') else content
  query = "ALTER SESSION SET TRANSACTION_ABORT_ON_ERROR=TRUE;BEGIN TRANSACTION;{0};INSERT INTO schema_history (script_name,repo_revision) values ('{1}','{2}');COMMIT;".format(content,file.name,repo_revision)
  execute_snowflake_query(snowflake_database,snowflake_schema,query,verbose)

if __name__ == '__main__':
  parser = argparse.ArgumentParser("Apply schema changes to a Snowflake data warehouse. Full readme at https://github.com/nib-health-funds/snowchange")
  parser.add_argument('-e', '--environment-name',type=str,help='The name of the environment (e.g. dev,test,prod)',required=True)
  parser.add_argument('-a', '--snowflake-account',type=str,help='The name of the snowflake account (e.g. ly12345)',required=True)
  parser.add_argument('-u', '--snowflake-user',type=str,help='The name of the snowflake user (e.g. deployer)',required=True)
  parser.add_argument('-r', '--snowflake-role',type=str,help='The name of the role to use (e.g. DEPLOYER_ROLE)',required=True)
  parser.add_argument('-w', '--snowflake-warehouse',type=str,help='The name of the warehouse to use (e.g. DEPLOYER_WAREHOUSE)',required=True)
  parser.add_argument('--snowflake-region',type=str,help='The name of the snowflake region (e.g. ap-southeast-2)',required=True)
  parser.add_argument('--repo-revision',type=str,help='A revision identifier for the repository. This is added to the schema_changes table for auditing purposes (e.g. ab18c3f)',required=True)
  parser.add_argument('-f','--root-folder', default=".",type=str,help='The folder in which to find the "databases" folder')
  parser.add_argument('-n','--database-naming-convention', default="{0}_{1}",type=str,help='The snowflake database naming convention, where {0} maps to the database folder name and {1} maps to the environment name supplied')
  
  parser.add_argument('-v','--verbose', type=bool, default=False)
  args = parser.parse_args()

  snowchange(args.environment_name,args.snowflake_account,args.snowflake_user,args.snowflake_role,args.snowflake_warehouse,args.snowflake_region,args.repo_revision,args.root_folder,args.database_naming_convention,args.verbose)
