from __future__ import annotations

import os
from pathlib import Path
from unittest import mock

import pytest

from schemachange.config.utils import get_snowflake_password

assets_path = Path(__file__).parent


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
