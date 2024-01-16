from __future__ import annotations


class SecretManager:
    """
    Provides the ability to redact secrets
    """

    __singleton: "SecretManager"

    @staticmethod
    def get_global_manager() -> "SecretManager":
        return SecretManager.__singleton

    @staticmethod
    def set_global_manager(global_manager: "SecretManager"):
        SecretManager.__singleton = global_manager

    @staticmethod
    def global_redact(context: str) -> str:
        """
        redacts any text that has been classified a secret
        using the global SecretManager instance.
        """
        return SecretManager.__singleton.redact(context)

    def __init__(self):
        self.__secrets = set()

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
