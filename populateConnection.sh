#!/bin/bash
# Script used in github actions to run test the schemachange functionality against the demo scenarios included in the repository.
touch ./connections.toml
echo [default] >> ./connections.toml
echo account = \"${SNOWFLAKE_ACCOUNT}\" >> ./connections.toml
echo user = \"${SNOWFLAKE_USER}\" >> ./connections.toml
echo role = \"${SNOWFLAKE_ROLE}\" >> ./connections.toml
echo warehouse = \"${SNOWFLAKE_WAREHOUSE}\" >> ./connections.toml
echo database = \"${SNOWFLAKE_DATABASE}\" >> ./connections.toml
echo password = \"${SNOWFLAKE_PASSWORD}\" >> ./connections.toml
echo "cat connections.toml"
cat ./connections.toml
