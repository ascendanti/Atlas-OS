"""
Atlas Personal OS - Task Tracker

A simple yet powerful task management system with priorities,
due dates, categories, and completion tracking.
"""

from __future__ import annotations

from datetime import datetime, date
from typing import Optional, List
from enum import Enum

from modules.core.database import Database, get_database
from modules.core.event_store import EventStore, get_event_store


class TaskStatus(Enum):
    """Task status values."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Task priority levels."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4


class TaskTracker:
    """Task management system."""

    TABLE_NAME = "tasks"
    SCHEMA = """
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        status TEXT DEFAULT 'pending',
        priority INTEGER DEFAULT 2,
        category TEXT,
        due_date DATE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP
    """

    def __init__(self, db: Optional[Database] = None, event_store: Optional[EventStore] = None):
        """Initialize task tracker with database and event store."""
        self.db = db or get_database()
        self.event_store = event_store or get_event_store()
        self._ensure_table()

    def _ensure_table(self) -> None:
        """Create tasks table if it doesn't exist."""
        self.db.create_table(self.TABLE_NAME, self.SCHEMA)

    def add(
        self,
        title: str,
        description: str = "",
        priority: TaskPriority = TaskPriority.MEDIUM,
        category: str = "",
        due_date: Optional[date] = None
    ) -> int:
        """
        Add a new task.

        Args:
            title: Task title
            description: Task description
            priority: Task priority level
            category: Task category/tag
            due_date: Due date for the task

        Returns:
            ID of the created task
        """
        data = {
            "title": title,
            "description": description,
            "priority": priority.value,
            "category": category,
            "due_date": due_date.isoformat() if due_date else None,
        }
        task_id = self.db.insert(self.TABLE_NAME, data)

        # Emit TASK_CREATED event (Event Spine invariant)
        self.event_store.emit(
            event_type="TASK_CREATED",
            entity_type="task",
            entity_id=task_id,
            payload={
                "title": title,
                "description": description,
                "priority": priority.value,
                "category": category,
                "due_date": due_date.isoformat() if due_date else None,
            }
        )
        return task_id

    def get(self, task_id: int) -> Optional[dict]:
        """
        Get a task by ID.

        Args:
            task_id: Task ID

        Returns:
            Task data or None if not found
        """
        row = self.db.fetchone(
            f"SELECT * FROM {self.TABLE_NAME} WHERE id = ?",
            (task_id,)
        )
        return dict(row) if row else None

    def list(
        self,
        status: Optional[TaskStatus] = None,
        category: Optional[str] = None,
        priority: Optional[TaskPriority] = None,
        limit: int = 100
    ) -> list[dict]:
        """
        List tasks with optional filters.

        Args:
            status: Filter by status
            category: Filter by category
            priority: Filter by priority
            limit: Maximum number of tasks to return

        Returns:
            List of task dictionaries
        """
        conditions = []
        params = []

        if status:
            conditions.append("status = ?")
            params.append(status.value)

        if category:
            conditions.append("category = ?")
            params.append(category)

        if priority:
            conditions.append("priority = ?")
            params.append(priority.value)

        where_clause = " AND ".join(conditions) if conditions else "1=1"
        sql = f"""
            SELECT * FROM {self.TABLE_NAME}
            WHERE {where_clause}
            ORDER BY priority DESC, due_date ASC NULLS LAST, created_at DESC
            LIMIT ?
        """
        params.append(limit)

        rows = self.db.fetchall(sql, tuple(params))
        return [dict(row) for row in rows]

    def update(self, task_id: int, **kwargs) -> bool:
        """
        Update a task.

        Args:
            task_id: Task ID to update
            **kwargs: Fields to update

        Returns:
            True if task was updated
        """
        if not kwargs:
            return False

        # Handle enum values
        if "priority" in kwargs and isinstance(kwargs["priority"], TaskPriority):
            kwargs["priority"] = kwargs["priority"].value
        if "status" in kwargs and isinstance(kwargs["status"], TaskStatus):
            kwargs["status"] = kwargs["status"].value
        if "due_date" in kwargs and isinstance(kwargs["due_date"], date):
            kwargs["due_date"] = kwargs["due_date"].isoformat()

        kwargs["updated_at"] = datetime.now().isoformat()

        rows_updated = self.db.update(
            self.TABLE_NAME,
            kwargs,
            "id = ?",
            (task_id,)
        )
        return rows_updated > 0

    def complete(self, task_id: int) -> bool:
        """
        Mark a task as completed.

        Args:
            task_id: Task ID to complete

        Returns:
            True if task was completed
        """
        return self.update(
            task_id,
            status=TaskStatus.COMPLETED,
            completed_at=datetime.now().isoformat()
        )

    def delete(self, task_id: int) -> bool:
        """
        Delete a task.

        Args:
            task_id: Task ID to delete

        Returns:
            True if task was deleted
        """
        rows_deleted = self.db.delete(
            self.TABLE_NAME,
            "id = ?",
            (task_id,)
        )
        return rows_deleted > 0

    def search(self, query: str) -> list[dict]:
        """
        Search tasks by title or description.

        Args:
            query: Search query

        Returns:
            Matching tasks
        """
        sql = f"""
            SELECT * FROM {self.TABLE_NAME}
            WHERE title LIKE ? OR description LIKE ?
            ORDER BY priority DESC, created_at DESC
        """
        pattern = f"%{query}%"
        rows = self.db.fetchall(sql, (pattern, pattern))
        return [dict(row) for row in rows]

    def get_due_today(self) -> list[dict]:
        """Get tasks due today."""
        today = date.today().isoformat()
        rows = self.db.fetchall(
            f"SELECT * FROM {self.TABLE_NAME} WHERE due_date = ? AND status != 'completed'",
            (today,)
        )
        return [dict(row) for row in rows]

    def get_overdue(self) -> list[dict]:
        """Get overdue tasks."""
        today = date.today().isoformat()
        rows = self.db.fetchall(
            f"SELECT * FROM {self.TABLE_NAME} WHERE due_date < ? AND status != 'completed'",
            (today,)
        )
        return [dict(row) for row in rows]

    def get_categories(self) -> list[str]:
        """Get all unique categories."""
        rows = self.db.fetchall(
            f"SELECT DISTINCT category FROM {self.TABLE_NAME} WHERE category IS NOT NULL AND category != ''"
        )
        return [row["category"] for row in rows]

    def count(self, status: Optional[TaskStatus] = None) -> int:
        """
        Count tasks.

        Args:
            status: Optional status filter

        Returns:
            Number of tasks
        """
        if status:
            row = self.db.fetchone(
                f"SELECT COUNT(*) as count FROM {self.TABLE_NAME} WHERE status = ?",
                (status.value,)
            )
        else:
            row = self.db.fetchone(f"SELECT COUNT(*) as count FROM {self.TABLE_NAME}")
        return row["count"] if row else 0
