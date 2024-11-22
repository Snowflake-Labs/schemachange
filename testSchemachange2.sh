#!/bin/bash
# Script used in github actions to run test the schemachange functionality against the demo scenarios included in the repository.
echo "::group::Setting up ${MY_TARGET_SCHEMA}"
schemachange deploy \
--config-folder ./demo \
--config-file-name schemachange-config-setup.yml \
--root-folder ./demo/${SCENARIO_NAME}/1_setup \
--connection-name default \
--connections-file-path ./connections.toml \
--verbose
echo "::endgroup::"

echo "::group::Testing Rendering to ${MY_TARGET_SCHEMA}"

schemachange render \
--config-folder ./demo/${SCENARIO_NAME} \
./demo/${SCENARIO_NAME}/2_test/A__render.sql
schemachange render \
--config-folder ./demo/${SCENARIO_NAME} \
./demo/${SCENARIO_NAME}/2_test/R__render.sql
schemachange render \
--config-folder ./demo/${SCENARIO_NAME} \
./demo/${SCENARIO_NAME}/2_test/V1.0.0__render.sql
echo "::endgroup::"

echo "::group::Testing Deployment using ${MY_TARGET_SCHEMA}"
set +e
schemachange deploy \
--config-folder ./demo/${SCENARIO_NAME} \
--connection-name default \
--connections-file-path ./connections.toml \
--root-folder ./demo/${SCENARIO_NAME}/2_test \
--verbose
RESULT=$?

if [ $RESULT -eq 0 ]; then
    echo "Deployment Completed!"
else
    echo "Deployment Failed. Proceeding to Teardown."
fi
    echo "::endgroup::"

set -e

echo "::group::Tearing down up ${MY_TARGET_SCHEMA}"
schemachange deploy \
--config-folder ./demo \
--config-file-name schemachange-config-teardown.yml \
--connection-name default \
--connections-file-path ./connections.toml \
--root-folder ./demo/${SCENARIO_NAME}/3_teardown \
--verbose
echo "::endgroup::"

if [ $RESULT -ne 0 ]; then
    exit 1
fi
