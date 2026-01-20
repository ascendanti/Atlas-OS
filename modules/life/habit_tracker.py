"""
Atlas Personal OS - Habit Tracker

Track daily habits, build streaks, and monitor consistency.
"""

from __future__ import annotations

from datetime import datetime, date, timedelta
from typing import Optional
from enum import Enum

from modules.core.database import Database, get_database


class HabitFrequency(Enum):
    """How often a habit should be performed."""
    DAILY = "daily"
    WEEKLY = "weekly"
    WEEKDAYS = "weekdays"
    WEEKENDS = "weekends"


class HabitTracker:
    """Daily habit tracking system."""

    HABITS_TABLE = "habits"
    HABITS_SCHEMA = """
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        frequency TEXT DEFAULT 'daily',
        target_count INTEGER DEFAULT 1,
        category TEXT,
        active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    """

    COMPLETIONS_TABLE = "habit_completions"
    COMPLETIONS_SCHEMA = """
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        habit_id INTEGER NOT NULL,
        completed_date DATE NOT NULL,
        count INTEGER DEFAULT 1,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (habit_id) REFERENCES habits(id),
        UNIQUE(habit_id, completed_date)
    """

    def __init__(self, db: Optional[Database] = None):
        """Initialize habit tracker with database."""
        self.db = db or get_database()
        self._ensure_tables()

    def _ensure_tables(self) -> None:
        """Create required tables if they don't exist."""
        self.db.create_table(self.HABITS_TABLE, self.HABITS_SCHEMA)
        self.db.create_table(self.COMPLETIONS_TABLE, self.COMPLETIONS_SCHEMA)

    def add_habit(
        self,
        name: str,
        description: str = "",
        frequency: HabitFrequency = HabitFrequency.DAILY,
        target_count: int = 1,
        category: str = ""
    ) -> int:
        """Add a new habit to track."""
        data = {
            "name": name,
            "description": description,
            "frequency": frequency.value,
            "target_count": target_count,
            "category": category,
        }
        return self.db.insert(self.HABITS_TABLE, data)

    def get_habit(self, habit_id: int) -> Optional[dict]:
        """Get a habit by ID."""
        row = self.db.fetchone(
            f"SELECT * FROM {self.HABITS_TABLE} WHERE id = ?",
            (habit_id,)
        )
        return dict(row) if row else None

    def list_habits(self, active_only: bool = True) -> list[dict]:
        """List all habits."""
        if active_only:
            rows = self.db.fetchall(
                f"SELECT * FROM {self.HABITS_TABLE} WHERE active = 1 ORDER BY name"
            )
        else:
            rows = self.db.fetchall(
                f"SELECT * FROM {self.HABITS_TABLE} ORDER BY name"
            )
        return [dict(row) for row in rows]

    def update_habit(self, habit_id: int, **kwargs) -> bool:
        """Update a habit."""
        if not kwargs:
            return False

        if "frequency" in kwargs and isinstance(kwargs["frequency"], HabitFrequency):
            kwargs["frequency"] = kwargs["frequency"].value

        rows_updated = self.db.update(
            self.HABITS_TABLE,
            kwargs,
            "id = ?",
            (habit_id,)
        )
        return rows_updated > 0

    def archive_habit(self, habit_id: int) -> bool:
        """Archive a habit (set inactive)."""
        return self.update_habit(habit_id, active=0)

    def delete_habit(self, habit_id: int) -> bool:
        """Delete a habit and all its completions."""
        with self.db.transaction():
            self.db.delete(self.COMPLETIONS_TABLE, "habit_id = ?", (habit_id,))
            rows_deleted = self.db.delete(self.HABITS_TABLE, "id = ?", (habit_id,))
        return rows_deleted > 0

    def complete_habit(
        self,
        habit_id: int,
        completed_date: Optional[date] = None,
        count: int = 1,
        notes: str = ""
    ) -> bool:
        """
        Mark a habit as completed for a date.

        Args:
            habit_id: Habit ID
            completed_date: Date of completion (default: today)
            count: Number of times completed (default: 1)
            notes: Optional notes

        Returns:
            True if recorded successfully
        """
        if completed_date is None:
            completed_date = date.today()

        # Check if already completed
        existing = self.db.fetchone(
            f"SELECT id, count FROM {self.COMPLETIONS_TABLE} WHERE habit_id = ? AND completed_date = ?",
            (habit_id, completed_date.isoformat())
        )

        if existing:
            # Update count
            new_count = existing["count"] + count
            return self.db.update(
                self.COMPLETIONS_TABLE,
                {"count": new_count, "notes": notes},
                "id = ?",
                (existing["id"],)
            ) > 0
        else:
            # Insert new completion
            data = {
                "habit_id": habit_id,
                "completed_date": completed_date.isoformat(),
                "count": count,
                "notes": notes,
            }
            self.db.insert(self.COMPLETIONS_TABLE, data)
            return True

    def uncomplete_habit(self, habit_id: int, completed_date: Optional[date] = None) -> bool:
        """Remove a habit completion for a date."""
        if completed_date is None:
            completed_date = date.today()

        rows_deleted = self.db.delete(
            self.COMPLETIONS_TABLE,
            "habit_id = ? AND completed_date = ?",
            (habit_id, completed_date.isoformat())
        )
        return rows_deleted > 0

    def is_completed(self, habit_id: int, check_date: Optional[date] = None) -> bool:
        """Check if a habit is completed for a date."""
        if check_date is None:
            check_date = date.today()

        habit = self.get_habit(habit_id)
        if not habit:
            return False

        row = self.db.fetchone(
            f"SELECT count FROM {self.COMPLETIONS_TABLE} WHERE habit_id = ? AND completed_date = ?",
            (habit_id, check_date.isoformat())
        )

        if not row:
            return False

        return row["count"] >= habit["target_count"]

    def get_streak(self, habit_id: int) -> int:
        """
        Get current streak for a habit.

        Returns:
            Number of consecutive days completed
        """
        habit = self.get_habit(habit_id)
        if not habit:
            return 0

        today = date.today()
        streak = 0
        check_date = today

        # Check if completed today, if not start from yesterday
        if not self.is_completed(habit_id, check_date):
            check_date = today - timedelta(days=1)
            if not self.is_completed(habit_id, check_date):
                return 0

        # Count backwards
        while self.is_completed(habit_id, check_date):
            streak += 1
            check_date -= timedelta(days=1)

        return streak

    def get_longest_streak(self, habit_id: int) -> int:
        """Get the longest streak ever for a habit."""
        rows = self.db.fetchall(
            f"SELECT completed_date FROM {self.COMPLETIONS_TABLE} WHERE habit_id = ? ORDER BY completed_date",
            (habit_id,)
        )

        if not rows:
            return 0

        dates = [date.fromisoformat(row["completed_date"]) for row in rows]

        longest = 1
        current = 1

        for i in range(1, len(dates)):
            if (dates[i] - dates[i-1]).days == 1:
                current += 1
                longest = max(longest, current)
            else:
                current = 1

        return longest

    def get_completion_rate(self, habit_id: int, days: int = 30) -> float:
        """
        Get completion rate for the last N days.

        Returns:
            Completion rate as decimal (0.0 to 1.0)
        """
        today = date.today()
        start_date = today - timedelta(days=days - 1)

        completions = self.db.fetchone(
            f"""SELECT COUNT(DISTINCT completed_date) as count
                FROM {self.COMPLETIONS_TABLE}
                WHERE habit_id = ? AND completed_date >= ?""",
            (habit_id, start_date.isoformat())
        )

        completed_days = completions["count"] if completions else 0
        return completed_days / days

    def get_today_status(self) -> list[dict]:
        """Get status of all active habits for today."""
        habits = self.list_habits(active_only=True)
        today = date.today()

        status = []
        for habit in habits:
            habit_status = habit.copy()
            habit_status["completed_today"] = self.is_completed(habit["id"], today)
            habit_status["current_streak"] = self.get_streak(habit["id"])
            status.append(habit_status)

        return status

    def get_completions_for_date(self, check_date: Optional[date] = None) -> list[dict]:
        """Get all completions for a specific date."""
        if check_date is None:
            check_date = date.today()

        rows = self.db.fetchall(
            f"""SELECT c.*, h.name as habit_name
                FROM {self.COMPLETIONS_TABLE} c
                JOIN {self.HABITS_TABLE} h ON c.habit_id = h.id
                WHERE c.completed_date = ?""",
            (check_date.isoformat(),)
        )
        return [dict(row) for row in rows]

    def get_weekly_summary(self, habit_id: int) -> dict:
        """Get a weekly summary for a habit."""
        today = date.today()
        start_of_week = today - timedelta(days=today.weekday())

        days_completed = 0
        total_count = 0

        for i in range(7):
            check_date = start_of_week + timedelta(days=i)
            if check_date > today:
                break

            row = self.db.fetchone(
                f"SELECT count FROM {self.COMPLETIONS_TABLE} WHERE habit_id = ? AND completed_date = ?",
                (habit_id, check_date.isoformat())
            )

            if row:
                days_completed += 1
                total_count += row["count"]

        return {
            "habit_id": habit_id,
            "week_start": start_of_week.isoformat(),
            "days_completed": days_completed,
            "total_count": total_count,
            "current_streak": self.get_streak(habit_id),
        }
