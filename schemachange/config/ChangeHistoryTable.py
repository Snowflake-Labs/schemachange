import dataclasses
from typing import ClassVar


@dataclasses.dataclass(frozen=True)
class ChangeHistoryTable:
    _default_database_name: ClassVar[str] = "METADATA"
    _default_schema_name: ClassVar[str] = "SCHEMACHANGE"
    _default_table_name: ClassVar[str] = "CHANGE_HISTORY"

    table_name: str = "CHANGE_HISTORY"
    schema_name: str = "SCHEMACHANGE"
    database_name: str = "METADATA"

    @property
    def fully_qualified(self) -> str:
        return f"{self.database_name}.{self.schema_name}.{self.table_name}"

    @classmethod
    def from_str(cls, table_str: str):
        details: dict[str, str] = {
            "database_name": cls._default_database_name,
            "schema_name": cls._default_schema_name,
            "table_name": cls._default_table_name,
        }
        if table_str is not None:
            table_name_parts = table_str.strip().split(".")
            if len(table_name_parts) == 1:
                details["table_name"] = table_name_parts[0]
            elif len(table_name_parts) == 2:
                details["table_name"] = table_name_parts[1]
                details["schema_name"] = table_name_parts[0]
            elif len(table_name_parts) == 3:
                details["table_name"] = table_name_parts[2]
                details["schema_name"] = table_name_parts[1]
                details["database_name"] = table_name_parts[0]
            else:
                raise ValueError(f"Invalid change history table name: {table_str}")

        # if the name element does not include '"' raise to upper case on return
        return cls(
            **{
                attr_name: attr_val if '"' in attr_val else attr_val.upper()
                for (attr_name, attr_val) in details.items()
            }
        )
