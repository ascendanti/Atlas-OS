"""
Atlas Personal OS - SQLite Database Manager

Provides a simple interface for SQLite database operations.
All data is stored locally in the data/ directory.
"""

import sqlite3
from pathlib import Path
from typing import Any, Optional
from contextlib import contextmanager


class Database:
    """SQLite database manager for Atlas Personal OS."""

    def __init__(self, db_name: str = "atlas.db", data_dir: Optional[Path] = None):
        """
        Initialize database connection.

        Args:
            db_name: Database filename (default: atlas.db)
            data_dir: Directory for database files (default: project/data/)
        """
        if data_dir is None:
            data_dir = Path(__file__).parent.parent.parent / "data"

        data_dir.mkdir(exist_ok=True)
        self.db_path = data_dir / db_name
        self._connection: Optional[sqlite3.Connection] = None

    @property
    def connection(self) -> sqlite3.Connection:
        """Get or create database connection."""
        if self._connection is None:
            self._connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self._connection.row_factory = sqlite3.Row
            # Enable foreign keys
            self._connection.execute("PRAGMA foreign_keys = ON")
        return self._connection

    def close(self) -> None:
        """Close database connection."""
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    @contextmanager
    def transaction(self):
        """Context manager for database transactions."""
        try:
            yield self.connection
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        """
        Execute SQL statement with parameters.

        Args:
            sql: SQL statement
            params: Parameters for the SQL statement

        Returns:
            Cursor object
        """
        return self.connection.execute(sql, params)

    def executemany(self, sql: str, params_list: list[tuple]) -> sqlite3.Cursor:
        """
        Execute SQL statement for multiple parameter sets.

        Args:
            sql: SQL statement
            params_list: List of parameter tuples

        Returns:
            Cursor object
        """
        return self.connection.executemany(sql, params_list)

    def fetchone(self, sql: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        """
        Execute query and fetch one result.

        Args:
            sql: SQL query
            params: Parameters for the query

        Returns:
            Single row or None
        """
        cursor = self.execute(sql, params)
        return cursor.fetchone()

    def fetchall(self, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
        """
        Execute query and fetch all results.

        Args:
            sql: SQL query
            params: Parameters for the query

        Returns:
            List of rows
        """
        cursor = self.execute(sql, params)
        return cursor.fetchall()

    def insert(self, table: str, data: dict[str, Any]) -> int:
        """
        Insert a row into a table.

        Args:
            table: Table name
            data: Dictionary of column names and values

        Returns:
            ID of inserted row
        """
        columns = ", ".join(data.keys())
        placeholders = ", ".join("?" * len(data))
        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"

        with self.transaction():
            cursor = self.execute(sql, tuple(data.values()))
            return cursor.lastrowid

    def update(self, table: str, data: dict[str, Any], where: str, params: tuple = ()) -> int:
        """
        Update rows in a table.

        Args:
            table: Table name
            data: Dictionary of column names and new values
            where: WHERE clause (without 'WHERE' keyword)
            params: Parameters for WHERE clause

        Returns:
            Number of rows updated
        """
        set_clause = ", ".join(f"{k} = ?" for k in data.keys())
        sql = f"UPDATE {table} SET {set_clause} WHERE {where}"

        with self.transaction():
            cursor = self.execute(sql, tuple(data.values()) + params)
            return cursor.rowcount

    def delete(self, table: str, where: str, params: tuple = ()) -> int:
        """
        Delete rows from a table.

        Args:
            table: Table name
            where: WHERE clause (without 'WHERE' keyword)
            params: Parameters for WHERE clause

        Returns:
            Number of rows deleted
        """
        sql = f"DELETE FROM {table} WHERE {where}"

        with self.transaction():
            cursor = self.execute(sql, params)
            return cursor.rowcount

    def table_exists(self, table: str) -> bool:
        """Check if a table exists."""
        result = self.fetchone(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table,)
        )
        return result is not None

    def create_table(self, table: str, schema: str) -> None:
        """
        Create a table if it doesn't exist.

        Args:
            table: Table name
            schema: Column definitions (e.g., "id INTEGER PRIMARY KEY, name TEXT")
        """
        sql = f"CREATE TABLE IF NOT EXISTS {table} ({schema})"
        with self.transaction():
            self.execute(sql)

    def migrate(self, migrations: list[str]) -> None:
        """
        Run a list of migration SQL statements.

        Args:
            migrations: List of SQL statements to execute
        """
        # Create migrations tracking table
        self.create_table(
            "_migrations",
            "id INTEGER PRIMARY KEY AUTOINCREMENT, sql_hash TEXT UNIQUE, applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
        )

        with self.transaction():
            for sql in migrations:
                sql_hash = str(hash(sql))
                # Check if migration already applied
                if self.fetchone("SELECT 1 FROM _migrations WHERE sql_hash = ?", (sql_hash,)):
                    continue
                # Apply migration
                self.execute(sql)
                self.execute("INSERT INTO _migrations (sql_hash) VALUES (?)", (sql_hash,))


# Singleton instance for easy access
_default_db: Optional[Database] = None


def get_database() -> Database:
    """Get the default database instance."""
    global _default_db
    if _default_db is None:
        _default_db = Database()
    return _default_db
