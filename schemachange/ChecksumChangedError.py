class ChecksumChangedError(Exception):
    """An applied versioned script no longer matches its recorded checksum."""

    def __init__(self, script_name: str, expected_checksum: str, current_checksum: str):
        super().__init__(
            f"Checksum has changed for applied versioned script: {script_name}\n"
            f"Expected checksum: {expected_checksum}\n"
            f"Current checksum:  {current_checksum}\n"
            "Restore the applied script and its rendering inputs. "
            "Put intended changes in a new versioned script."
        )
