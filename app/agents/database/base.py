from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    pass


class DatabaseConnector(ABC):
    """Abstract base for database metadata and status queries."""

    @abstractmethod
    def list_databases(self) -> dict:
        """Return all databases on the server as {"databases": [...]}."""

    @abstractmethod
    def list_tables(self, database: str) -> dict:
        """Return tables in a database as {"database": ..., "tables": [...]}."""

    @abstractmethod
    def describe_table(self, database: str, table: str) -> dict:
        """Return column info as {"database": ..., "table": ..., "columns": [...]}."""

    @abstractmethod
    def get_database_status(self) -> dict:
        """Return server runtime status for troubleshooting."""

    @abstractmethod
    def close(self) -> None:
        """Release the underlying connection."""

    def __enter__(self) -> "DatabaseConnector":
        return self

    def __exit__(self, *_) -> None:
        self.close()

    @classmethod
    def create(
        cls,
        db_type: Literal["mysql", "postgresql"],
        host: str,
        port: int,
        user: str,
        password: str,
    ) -> "DatabaseConnector":
        """Factory: return a connector for the given db_type."""
        if db_type == "mysql":
            from app.agents.database.mysql import MySQLConnector
            return MySQLConnector(host=host, port=port, user=user, password=password)
        if db_type == "postgresql":
            from app.agents.database.postgres import PostgreSQLConnector
            return PostgreSQLConnector(host=host, port=port, user=user, password=password)
        raise ValueError(f"Unsupported db_type: {db_type!r}. Use 'mysql' or 'postgresql'.")
