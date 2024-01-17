import json
import os
import warnings

import requests
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization


def get_snowflake_password() -> str | None:
    snowflake_password = None
    if os.getenv("SNOWFLAKE_PASSWORD") is not None and os.getenv("SNOWFLAKE_PASSWORD"):
        snowflake_password = os.getenv("SNOWFLAKE_PASSWORD")

    # Check legacy/deprecated env variable
    if os.getenv("SNOWSQL_PWD") is not None and os.getenv("SNOWSQL_PWD"):
        if snowflake_password:
            warnings.warn(
                "Environment variables SNOWFLAKE_PASSWORD and SNOWSQL_PWD "
                "are both present, using SNOWFLAKE_PASSWORD"
            )
        else:
            warnings.warn(
                "The SNOWSQL_PWD environment variable is deprecated and "
                "will be removed in a later version of schemachange. "
                "Please use SNOWFLAKE_PASSWORD instead.",
                DeprecationWarning,
            )
            snowflake_password = os.getenv("SNOWSQL_PWD")
    return snowflake_password


def get_private_key_password(verbose: bool) -> bytes | None:
    private_key_password = os.getenv("SNOWFLAKE_PRIVATE_KEY_PASSPHRASE", "")

    if private_key_password:
        return private_key_password.encode()

    if verbose:
        print("No private key passphrase provided. Assuming the key is not encrypted.")

    return None


def get_private_key_bytes(verbose: bool) -> bytes:
    private_key_password = get_private_key_password(verbose=verbose)
    with open(os.environ["SNOWFLAKE_PRIVATE_KEY_PATH"], "rb") as key:
        p_key = serialization.load_pem_private_key(
            key.read(),
            password=private_key_password,
            backend=default_backend(),
        )

    return p_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )


def get_oauth_token(oauth_config: dict):
    req_info = {
        "url": oauth_config["token-provider-url"],
        "headers": oauth_config["token-request-headers"],
        "data": oauth_config["token-request-payload"],
    }
    token_name = oauth_config["token-response-name"]
    response = requests.post(**req_info)
    resJsonDict = json.loads(response.text)
    try:
        return resJsonDict[token_name]
    except KeyError:
        keys = ", ".join(resJsonDict.keys())
        errormessage = f"Response Json contains keys: {keys} \n but not {token_name}"
        # if there is an error passed with the response include that
        if "error_description" in resJsonDict.keys():
            errormessage = f"{errormessage}\n error description: {resJsonDict['error_description']}"
        raise KeyError(errormessage)
