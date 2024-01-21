import json
import os
from unittest import mock
from unittest.mock import MagicMock

import pytest
import structlog

from schemachange.session.Credential import (
    credential_factory,
    PasswordCredential,
    ExternalBrowserCredential,
    OktaCredential,
    PrivateKeyCredential,
    OauthCredential,
)


@pytest.mark.parametrize(
    "env_vars, oauth_config, expected",
    [
        (
            {"SNOWFLAKE_PASSWORD": "my-password"},
            None,
            PasswordCredential(password="my-password"),
        ),
        (
            {
                "SNOWFLAKE_PASSWORD": "my-password",
                "SNOWFLAKE_AUTHENTICATOR": "snowflake",
            },
            None,
            PasswordCredential(password="my-password"),
        ),
        (
            {
                "SNOWFLAKE_AUTHENTICATOR": "oauth",
            },
            {
                "token-provider-url": "token-provider-url-from-yaml",
                "token-response-name": "token-response-name-from-yaml",
                "token-request-headers": {
                    "Content-Type": "Content-Type-from-yaml",
                    "User-Agent": "User-Agent-from-yaml",
                },
                "token-request-payload": {
                    "client_id": "id-from-yaml",
                    "username": "username-from-yaml",
                    "password": "password-from-yaml",
                    "grant_type": "type-from-yaml",
                    "scope": "scope-from-yaml",
                },
            },
            OauthCredential(token="my-token"),
        ),
        (
            {
                "SNOWFLAKE_AUTHENTICATOR": "externalbrowser",
            },
            None,
            ExternalBrowserCredential(),
        ),
        (
            {
                "SNOWFLAKE_AUTHENTICATOR": "https://someurl.com",
                "SNOWFLAKE_PASSWORD": "my-password",
            },
            None,
            OktaCredential(authenticator="https://someurl.com", password="my-password"),
        ),
        (
            {
                "SNOWFLAKE_PRIVATE_KEY_PATH": "some_path",
                "SNOWFLAKE_AUTHENTICATOR": "snowflake",
            },
            None,
            PrivateKeyCredential(private_key="some_path"),
        ),
    ],
)
@mock.patch(
    "schemachange.session.Credential.get_private_key_bytes",
    return_value="some_path",
)
@mock.patch("requests.post")
def test_credential_factory(
    mock_post, _, env_vars: dict, oauth_config: dict | None, expected: str
):
    mock_response = MagicMock()
    mock_response.text = json.dumps({"token-response-name-from-yaml": "my-token"})
    mock_post.return_value = mock_response
    logger = structlog.testing.CapturingLogger()

    with mock.patch.dict(os.environ, env_vars, clear=True):
        # noinspection PyTypeChecker
        result = credential_factory(oauth_config=oauth_config, logger=logger)
        assert result == expected


@pytest.mark.parametrize("env_vars", [{}])
def test_credential_factory_unhandled(env_vars):
    logger = structlog.testing.CapturingLogger()
    with pytest.raises(NameError):
        with mock.patch.dict(os.environ, env_vars, clear=True):
            # noinspection PyTypeChecker
            credential_factory(logger=logger)
