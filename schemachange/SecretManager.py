from __future__ import annotations

import structlog

logger = structlog.getLogger(__name__)


def extract_config_secrets(config_vars: dict[str, dict | str] | None) -> set[str]:
    """
    Extracts all secret values from the vars attributes in config
    """

    # defined as an inner/ nested function to provide encapsulation
    def inner_extract_dictionary_secrets(
        dictionary: dict[str, dict | str], child_of_secrets: bool = False
    ) -> set[str]:
        """
        Considers any key with the word secret in the name as a secret or
        all values as secrets if a child of a key named secrets.
        """
        extracted_secrets: set[str] = set()

        if dictionary:
            for key, value in dictionary.items():
                if isinstance(value, dict):
                    if key == "secrets":
                        extracted_secrets = (
                            extracted_secrets
                            | inner_extract_dictionary_secrets(value, True)
                        )
                    else:
                        extracted_secrets = (
                            extracted_secrets
                            | inner_extract_dictionary_secrets(value, child_of_secrets)
                        )
                elif child_of_secrets or "SECRET" in key.upper():
                    extracted_secrets.add(value.strip())
        return extracted_secrets

    extracted = set()

    if config_vars:
        extracted = inner_extract_dictionary_secrets(config_vars)
    return extracted


class SecretManager:
    """
    Provides the ability to redact secrets
    """

    __secrets: set

    def __init__(self, config_vars: dict[str, dict | str] | None = None):
        self.__secrets = set()
        secrets = extract_config_secrets(config_vars=config_vars)
        self.add_range(secrets=secrets)

    def clear(self):
        self.__secrets = set()

    def add(self, secret: str):
        if secret:
            self.__secrets.add(secret)

    def add_range(self, secrets: set[str] | None):
        if secrets:
            self.__secrets = self.__secrets | secrets

    def redact(self, context: str | None) -> str:
        """
        redacts any text that has been classified a secret
        """
        redacted = context
        if redacted:
            for secret in self.__secrets:
                redacted = redacted.replace(secret, "*" * len(secret))
        return redacted
