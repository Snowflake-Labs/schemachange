import os
from unittest import mock

import pytest

from schemachange.session.utils import (
    get_snowflake_password,
    get_private_key_password,
)


@pytest.mark.parametrize(
    "env_vars, expected",
    [
        ({"SNOWFLAKE_PASSWORD": "my-password"}, "my-password"),
        ({"SNOWFLAKE_PASSWORD": ""}, None),
        ({}, None),
        ({"SNOWSQL_PWD": "my-password"}, "my-password"),
        (
            {"SNOWSQL_PWD": "my-password", "SNOWFLAKE_PASSWORD": "my-password"},
            "my-password",
        ),
    ],
)
def test_get_snowflake_password(env_vars: dict, expected: str):
    with mock.patch.dict(os.environ, env_vars, clear=True):
        result = get_snowflake_password()
        assert result == expected


@pytest.mark.parametrize(
    "env_vars, expected",
    [
        ({"SNOWFLAKE_PRIVATE_KEY_PASSPHRASE": "my-passphrase"}, b"my-passphrase"),
        ({}, None),
    ],
)
def test_get_private_key_password(env_vars: dict, expected: str):
    with mock.patch.dict(os.environ, env_vars, clear=True):
        result = get_private_key_password(verbose=False)
        assert result == expected
