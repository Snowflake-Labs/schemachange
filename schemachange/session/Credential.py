import os
from abc import ABC
from typing import Literal, Annotated

import structlog
from pydantic import BaseModel, UrlConstraints
from pydantic_core import Url

from schemachange.session.utils import (
    get_snowflake_password,
    get_private_key_bytes,
    get_oauth_token,
)

HttpsUrl = Annotated[
    Url,
    UrlConstraints(allowed_schemes=["https"]),
]

logger = structlog.getLogger(__name__)


class Credential(BaseModel, ABC):
    authenticator: Literal["snowflake", "oauth", "externalbrowser"] | HttpsUrl


class OauthCredential(Credential):
    authenticator: Literal["oauth"] = "oauth"
    token: str


class PasswordCredential(Credential):
    authenticator: Literal["snowflake"] = "snowflake"
    password: str


class PrivateKeyCredential(Credential):
    authenticator: Literal["snowflake"] = "snowflake"
    private_key: str


class ExternalBrowserCredential(Credential):
    authenticator: Literal["externalbrowser"] = "externalbrowser"
    password: str | None = None


class OktaCredential(Credential):
    authenticator: HttpsUrl
    password: str


def credential_factory(
    oauth_config: dict | None = None,
) -> (
    OauthCredential
    | PasswordCredential
    | ExternalBrowserCredential
    | OktaCredential
    | PrivateKeyCredential
):
    snowflake_authenticator = os.getenv("SNOWFLAKE_AUTHENTICATOR")
    if not snowflake_authenticator:
        snowflake_authenticator = "snowflake"

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


SomeCredential = (
    OauthCredential
    | PasswordCredential
    | ExternalBrowserCredential
    | OktaCredential
    | PrivateKeyCredential
)
