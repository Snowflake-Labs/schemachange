from __future__ import annotations

from schemachange.Config import Config


def extract_config_secrets(config: Config | None) -> set[str]:
    """
    Extracts all secret values from the vars attributes in config
    """

    # defined as an inner/ nested function to provide encapsulation
    def inner_extract_dictionary_secrets(
        dictionary: dict[str, object], child_of_secrets: bool = False
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

    if config:
        extracted = inner_extract_dictionary_secrets(config.vars)
    return extracted
