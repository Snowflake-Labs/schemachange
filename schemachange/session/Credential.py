from __future__ import annotations

import dataclasses
import os
from typing import Literal, Union

import structlog

from schemachange.session.utils import (
    get_snowflake_password,
    get_private_key_bytes,
    get_oauth_token,
)


@dataclasses.dataclass(frozen=True)
class OauthCredential:
    token: str
    authenticator: Literal["oauth"] = "oauth"


@dataclasses.dataclass(frozen=True)
class PasswordCredential:
    password: str
    authenticator: Literal["snowflake"] = "snowflake"


@dataclasses.dataclass(frozen=True)
class PrivateKeyCredential:
    private_key: bytes
    authenticator: Literal["snowflake"] = "snowflake"


@dataclasses.dataclass(frozen=True)
class ExternalBrowserCredential:
    password: str | None = None
    authenticator: Literal["externalbrowser"] = "externalbrowser"


@dataclasses.dataclass(frozen=True)
class OktaCredential:
    authenticator: str
    password: str


SomeCredential = Union[
    OauthCredential,
    PasswordCredential,
    ExternalBrowserCredential,
    OktaCredential,
    PrivateKeyCredential,
]


def credential_factory(
    logger: structlog.BoundLogger,
    oauth_config: dict | None = None,
) -> SomeCredential:
    snowflake_authenticator = os.getenv("SNOWFLAKE_AUTHENTICATOR", default="snowflake")

    # OAuth based authentication
    if snowflake_authenticator.lower() == "oauth":
        logger.debug("Proceeding with Oauth Access Token authentication")
        return OauthCredential(token=get_oauth_token(oauth_config))

    # External Browser based SSO
    if snowflake_authenticator.lower() == "externalbrowser":
        logger.debug("Proceeding with External Browser authentication")
        return ExternalBrowserCredential()

    snowflake_password = get_snowflake_password()

    # IDP based Authentication, limited to Okta
    if snowflake_authenticator.lower()[:8] == "https://":
        logger.debug(
            "Proceeding with Okta authentication", okta_endpoint=snowflake_authenticator
        )
        return OktaCredential(
            authenticator=snowflake_authenticator, password=snowflake_password
        )

    if snowflake_authenticator.lower() != "snowflake":
        logger.debug(
            "Supplied authenticator is not supported authenticator option. Choose from snowflake, "
            "externalbrowser, oauth, https://<subdomain>.okta.com. "
            "Using default value = 'snowflake'",
            snowflake_authenticator=snowflake_authenticator,
        )

    if snowflake_password:
        logger.debug("Proceeding with password authentication")

        return PasswordCredential(password=snowflake_password)

    if os.getenv("SNOWFLAKE_PRIVATE_KEY_PATH", ""):
        logger.debug("Proceeding with private key authentication")

        return PrivateKeyCredential(private_key=get_private_key_bytes())

    raise NameError(
        "Missing environment variable(s). \n"
        "SNOWFLAKE_PASSWORD must be defined for password authentication. \n"
        "SNOWFLAKE_PRIVATE_KEY_PATH and (optional) SNOWFLAKE_PRIVATE_KEY_PASSPHRASE "
        "must be defined for private key authentication. \n"
        "SNOWFLAKE_AUTHENTICATOR must be defined is using Oauth, OKTA or external Browser Authentication."
    )
