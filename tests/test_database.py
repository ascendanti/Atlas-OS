"""
Tests for the Database module.
"""

import pytest
from modules.core.database import Database


class TestDatabase:
    """Tests for Database class."""

    def test_create_table(self, temp_db):
        """Test creating a table."""
        temp_db.create_table("test_table", "id INTEGER PRIMARY KEY, name TEXT")
        assert temp_db.table_exists("test_table")

    def test_insert_and_fetch(self, temp_db):
        """Test inserting and fetching data."""
        temp_db.create_table("users", "id INTEGER PRIMARY KEY, name TEXT, age INTEGER")

        user_id = temp_db.insert("users", {"name": "Alice", "age": 30})
        assert user_id == 1

        row = temp_db.fetchone("SELECT * FROM users WHERE id = ?", (1,))
        assert row["name"] == "Alice"
        assert row["age"] == 30

    def test_fetchall(self, temp_db):
        """Test fetching all rows."""
        temp_db.create_table("items", "id INTEGER PRIMARY KEY, name TEXT")
        temp_db.insert("items", {"name": "Item 1"})
        temp_db.insert("items", {"name": "Item 2"})
        temp_db.insert("items", {"name": "Item 3"})

        rows = temp_db.fetchall("SELECT * FROM items ORDER BY id")
        assert len(rows) == 3
        assert rows[0]["name"] == "Item 1"
        assert rows[2]["name"] == "Item 3"

    def test_update(self, temp_db):
        """Test updating data."""
        temp_db.create_table("users", "id INTEGER PRIMARY KEY, name TEXT")
        temp_db.insert("users", {"name": "Bob"})

        rows_updated = temp_db.update("users", {"name": "Robert"}, "id = ?", (1,))
        assert rows_updated == 1

        row = temp_db.fetchone("SELECT * FROM users WHERE id = ?", (1,))
        assert row["name"] == "Robert"

    def test_delete(self, temp_db):
        """Test deleting data."""
        temp_db.create_table("items", "id INTEGER PRIMARY KEY, name TEXT")
        temp_db.insert("items", {"name": "To Delete"})

        rows_deleted = temp_db.delete("items", "id = ?", (1,))
        assert rows_deleted == 1

        row = temp_db.fetchone("SELECT * FROM items WHERE id = ?", (1,))
        assert row is None

    def test_table_exists_false(self, temp_db):
        """Test table_exists returns False for non-existent table."""
        assert not temp_db.table_exists("nonexistent_table")

    def test_transaction_commit(self, temp_db):
        """Test transaction commits successfully."""
        temp_db.create_table("test", "id INTEGER PRIMARY KEY, value TEXT")

        with temp_db.transaction():
            temp_db.execute("INSERT INTO test (value) VALUES (?)", ("test_value",))

        row = temp_db.fetchone("SELECT * FROM test")
        assert row["value"] == "test_value"

    def test_transaction_rollback(self, temp_db):
        """Test transaction rollback on error."""
        temp_db.create_table("test", "id INTEGER PRIMARY KEY, value TEXT NOT NULL")

        try:
            with temp_db.transaction():
                temp_db.execute("INSERT INTO test (value) VALUES (?)", ("good",))
                temp_db.execute("INSERT INTO test (value) VALUES (?)", (None,))  # Should fail
        except Exception:
            pass

        rows = temp_db.fetchall("SELECT * FROM test")
        assert len(rows) == 0  # Rollback should have occurred

    def test_migrate(self, temp_db):
        """Test running migrations."""
        migrations = [
            "CREATE TABLE migration_test (id INTEGER PRIMARY KEY, name TEXT)",
            "ALTER TABLE migration_test ADD COLUMN email TEXT",
        ]

        temp_db.migrate(migrations)
        assert temp_db.table_exists("migration_test")

        # Running same migrations again should be idempotent
        temp_db.migrate(migrations)  # Should not raise
