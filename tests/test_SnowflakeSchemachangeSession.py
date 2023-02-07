import os 
import unittest.mock as mock 

import pytest

import schemachange.cli

#region authenticate(self):


@mock.patch.dict(os.environ, {})
def test__SnowflakeSchemachangeSession_noauth_set():
  pass

@mock.patch.dict(os.environ, {"SNOWFLAKE_AUTHENTICATOR":  'externalbrowser' })
def test__SnowflakeSchemachangeSession_externalBrowser_set():
  pass

@mock.patch.dict(os.environ, { "SNOWFLAKE_AUTHENTICATOR":  'https://someorg.okta.com' })
def test__SnowflakeSchemachangeSession_okta_set():
  pass

@mock.patch.dict(os.environ, {"SNOWFLAKE_PASSWORD":  'Somepass' })
def test__SnowflakeSchemachangeSession_password_set():
  pass

@mock.patch.dict(os.environ, { "SNOWFLAKE_AUTHENTICATOR":  'oath' })
def test__SnowflakeSchemachangeSession_oauth_set():
  pass

@mock.patch.dict(os.environ, { "SNOWFLAKE_PRIVATE_KEY_PASSPHRASE":  'Passphrase', "SNOWFLAKE_PRIVATE_KEY_PATH":'Somepath' })
def test__SnowflakeSchemachangeSession_privatekey_set():
  pass
# do we need precedence of order tested?

#endregion authenticate(self):

#region get_oauth_token(self):


def test__get_oauth_token_sucess():
  pass

def test__get_oauth_token_fail_wrong_token_key():
  pass

def test__get_oauth_token_fail_other():
  pass

#endregion get_oauth_token(self):




#  def execute_snowflake_query(self, query):
 
#  def fetch_change_history_metadata(self,change_history_table):

#  def create_change_history_table_if_missing(self, change_history_table):
 
#  def fetch_r_scripts_checksum(self,change_history_table):

#  def fetch_change_history(self, change_history_table):
  
#  def append_string_to_query_tag(self,tag_string):

#  def reset_query_tag(self):

# apply_change_script(self, script, script_content, change_history_table):