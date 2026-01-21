"""
Atlas Personal OS - Enhanced Task Tracker

Full-featured task management with:
- Subtasks (hierarchical tasks)
- Multiple tags
- Time estimates & tracking
- Dependencies (blocked_by)
- Recurring tasks
- Projects & milestones
- GTD views (Today/Upcoming/Someday)
- Goal linkage
"""

from __future__ import annotations
from datetime import datetime, date, timedelta
from typing import Optional, List
from enum import Enum
import json

from modules.core.database import Database, get_database
from modules.core.event_store import EventStore, get_event_store


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"
    WAITING = "waiting"
    SOMEDAY = "someday"


class TaskPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4


class RecurrenceType(Enum):
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class TaskTracker:
    """Enhanced task management system."""

    TABLE_NAME = "tasks"
    SCHEMA = """
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        status TEXT DEFAULT 'pending',
        priority INTEGER DEFAULT 2,
        due_date DATE,
        scheduled_date DATE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP,
        -- Hierarchy
        parent_id INTEGER REFERENCES tasks(id),
        project_id INTEGER,
        goal_id INTEGER,
        -- Tags (JSON array)
        tags TEXT DEFAULT '[]',
        -- Time tracking
        estimated_minutes INTEGER,
        actual_minutes INTEGER DEFAULT 0,
        -- Recurrence
        recurrence_type TEXT DEFAULT 'none',
        recurrence_interval INTEGER DEFAULT 1,
        recurrence_end_date DATE,
        -- Dependencies (JSON array of task IDs)
        blocked_by TEXT DEFAULT '[]',
        -- Context
        energy_level TEXT,
        context TEXT
    """

    def __init__(self, db: Optional[Database] = None, event_store: Optional[EventStore] = None):
        self.db = db or get_database()
        self.event_store = event_store or get_event_store()
        self._ensure_table()

    def _ensure_table(self) -> None:
        self.db.create_table(self.TABLE_NAME, self.SCHEMA)
        # Add columns if they don't exist (migration)
        self._migrate_schema()

    def _migrate_schema(self) -> None:
        """Add new columns to existing tables."""
        new_columns = [
            ("parent_id", "INTEGER"),
            ("project_id", "INTEGER"),
            ("goal_id", "INTEGER"),
            ("tags", "TEXT DEFAULT '[]'"),
            ("estimated_minutes", "INTEGER"),
            ("actual_minutes", "INTEGER DEFAULT 0"),
            ("recurrence_type", "TEXT DEFAULT 'none'"),
            ("recurrence_interval", "INTEGER DEFAULT 1"),
            ("recurrence_end_date", "DATE"),
            ("blocked_by", "TEXT DEFAULT '[]'"),
            ("energy_level", "TEXT"),
            ("context", "TEXT"),
            ("scheduled_date", "DATE"),
        ]
        for col_name, col_type in new_columns:
            try:
                self.db.execute(f"ALTER TABLE {self.TABLE_NAME} ADD COLUMN {col_name} {col_type}")
                self.db.connection.commit()
            except:
                pass  # Column already exists

    def add(
        self,
        title: str,
        description: str = "",
        priority: TaskPriority = TaskPriority.MEDIUM,
        due_date: Optional[date] = None,
        scheduled_date: Optional[date] = None,
        parent_id: Optional[int] = None,
        project_id: Optional[int] = None,
        goal_id: Optional[int] = None,
        tags: List[str] = None,
        estimated_minutes: Optional[int] = None,
        recurrence_type: RecurrenceType = RecurrenceType.NONE,
        recurrence_interval: int = 1,
        blocked_by: List[int] = None,
        energy_level: str = "",
        context: str = "",
        category: str = ""  # Backward compatibility
    ) -> int:
        """Add a new task with all options."""
        tags = tags or []
        if category and category not in tags:
            tags.append(category)
        blocked_by = blocked_by or []

        data = {
            "title": title,
            "description": description,
            "priority": priority.value,
            "due_date": due_date.isoformat() if due_date else None,
            "scheduled_date": scheduled_date.isoformat() if scheduled_date else None,
            "parent_id": parent_id,
            "project_id": project_id,
            "goal_id": goal_id,
            "tags": json.dumps(tags),
            "estimated_minutes": estimated_minutes,
            "recurrence_type": recurrence_type.value,
            "recurrence_interval": recurrence_interval,
            "blocked_by": json.dumps(blocked_by),
            "energy_level": energy_level,
            "context": context,
        }
        task_id = self.db.insert(self.TABLE_NAME, data)

        self.event_store.emit("TASK_CREATED", "task", task_id, {
            "title": title, "priority": priority.value,
            "due_date": data["due_date"], "tags": tags,
            "parent_id": parent_id, "goal_id": goal_id,
        })
        return task_id

    def get(self, task_id: int) -> Optional[dict]:
        """Get a task by ID."""
        row = self.db.fetchone(f"SELECT * FROM {self.TABLE_NAME} WHERE id = ?", (task_id,))
        return self._parse_task(row) if row else None

    def _parse_task(self, row) -> dict:
        """Parse task row, handling JSON fields."""
        task = dict(row)
        task["tags"] = json.loads(task.get("tags") or "[]")
        task["blocked_by"] = json.loads(task.get("blocked_by") or "[]")
        # Backward compatibility
        task["category"] = task["tags"][0] if task["tags"] else ""
        return task

    def list(
        self,
        status: Optional[str] = None,
        priority: Optional[TaskPriority] = None,
        tag: Optional[str] = None,
        project_id: Optional[int] = None,
        goal_id: Optional[int] = None,
        parent_id: Optional[int] = None,
        include_subtasks: bool = True,
        limit: int = 100,
        category: Optional[str] = None  # Backward compat
    ) -> list[dict]:
        """List tasks with filters."""
        conditions = []
        params = []

        if status:
            conditions.append("status = ?")
            params.append(status if isinstance(status, str) else status.value)
        if priority:
            conditions.append("priority = ?")
            params.append(priority.value)
        if tag or category:
            t = tag or category
            conditions.append("tags LIKE ?")
            params.append(f'%"{t}"%')
        if project_id:
            conditions.append("project_id = ?")
            params.append(project_id)
        if goal_id:
            conditions.append("goal_id = ?")
            params.append(goal_id)
        if parent_id is not None:
            conditions.append("parent_id = ?")
            params.append(parent_id)
        elif not include_subtasks:
            conditions.append("parent_id IS NULL")

        where = " AND ".join(conditions) if conditions else "1=1"
        sql = f"""SELECT * FROM {self.TABLE_NAME} WHERE {where}
                  ORDER BY priority DESC, due_date ASC NULLS LAST, created_at DESC LIMIT ?"""
        params.append(limit)

        rows = self.db.fetchall(sql, tuple(params))
        return [self._parse_task(row) for row in rows]

    def update(self, task_id: int, **kwargs) -> bool:
        """Update task fields."""
        if not kwargs:
            return False

        if "priority" in kwargs and isinstance(kwargs["priority"], TaskPriority):
            kwargs["priority"] = kwargs["priority"].value
        if "status" in kwargs and isinstance(kwargs["status"], TaskStatus):
            kwargs["status"] = kwargs["status"].value
        if "due_date" in kwargs and isinstance(kwargs["due_date"], date):
            kwargs["due_date"] = kwargs["due_date"].isoformat()
        if "scheduled_date" in kwargs and isinstance(kwargs["scheduled_date"], date):
            kwargs["scheduled_date"] = kwargs["scheduled_date"].isoformat()
        if "tags" in kwargs and isinstance(kwargs["tags"], list):
            kwargs["tags"] = json.dumps(kwargs["tags"])
        if "blocked_by" in kwargs and isinstance(kwargs["blocked_by"], list):
            kwargs["blocked_by"] = json.dumps(kwargs["blocked_by"])
        if "recurrence_type" in kwargs and isinstance(kwargs["recurrence_type"], RecurrenceType):
            kwargs["recurrence_type"] = kwargs["recurrence_type"].value

        kwargs["updated_at"] = datetime.now().isoformat()
        return self.db.update(self.TABLE_NAME, kwargs, "id = ?", (task_id,)) > 0

    def complete(self, task_id: int) -> bool:
        """Mark task completed. Creates next occurrence if recurring."""
        task = self.get(task_id)
        if not task:
            return False

        completed_at = datetime.now().isoformat()
        result = self.update(task_id, status=TaskStatus.COMPLETED, completed_at=completed_at)

        if result:
            self.event_store.emit("TASK_COMPLETED", "task", task_id, {
                "title": task["title"], "completed_at": completed_at,
                "actual_minutes": task.get("actual_minutes", 0),
            })
            # Handle recurrence
            if task.get("recurrence_type") and task["recurrence_type"] != "none":
                self._create_next_occurrence(task)
            # Complete subtasks
            subtasks = self.get_subtasks(task_id)
            for st in subtasks:
                if st["status"] != "completed":
                    self.complete(st["id"])
        return result

    def _create_next_occurrence(self, task: dict) -> Optional[int]:
        """Create next occurrence of a recurring task."""
        rec_type = task["recurrence_type"]
        interval = task.get("recurrence_interval", 1)
        base_date = date.fromisoformat(task["due_date"]) if task.get("due_date") else date.today()

        if rec_type == "daily":
            next_date = base_date + timedelta(days=interval)
        elif rec_type == "weekly":
            next_date = base_date + timedelta(weeks=interval)
        elif rec_type == "biweekly":
            next_date = base_date + timedelta(weeks=2 * interval)
        elif rec_type == "monthly":
            next_date = base_date.replace(month=base_date.month + interval)
        elif rec_type == "yearly":
            next_date = base_date.replace(year=base_date.year + interval)
        else:
            return None

        # Check recurrence end date
        if task.get("recurrence_end_date"):
            end = date.fromisoformat(task["recurrence_end_date"])
            if next_date > end:
                return None

        return self.add(
            title=task["title"], description=task.get("description", ""),
            priority=TaskPriority(task["priority"]), due_date=next_date,
            project_id=task.get("project_id"), goal_id=task.get("goal_id"),
            tags=task.get("tags", []), estimated_minutes=task.get("estimated_minutes"),
            recurrence_type=RecurrenceType(rec_type), recurrence_interval=interval,
            context=task.get("context", ""), energy_level=task.get("energy_level", ""),
        )

    # === Subtasks ===
    def add_subtask(self, parent_id: int, title: str, **kwargs) -> int:
        """Add a subtask to a parent task."""
        parent = self.get(parent_id)
        if not parent:
            raise ValueError(f"Parent task {parent_id} not found")
        return self.add(title=title, parent_id=parent_id, project_id=parent.get("project_id"),
                        goal_id=parent.get("goal_id"), **kwargs)

    def get_subtasks(self, task_id: int) -> list[dict]:
        """Get all subtasks of a task."""
        return self.list(parent_id=task_id, include_subtasks=True, limit=1000)

    # === Time Tracking ===
    def log_time(self, task_id: int, minutes: int) -> bool:
        """Log time spent on a task."""
        task = self.get(task_id)
        if not task:
            return False
        new_total = (task.get("actual_minutes") or 0) + minutes
        result = self.update(task_id, actual_minutes=new_total)
        if result:
            self.event_store.emit("TASK_TIME_LOGGED", "task", task_id, {
                "minutes": minutes, "total_minutes": new_total,
            })
        return result

    # === Dependencies ===
    def add_dependency(self, task_id: int, blocked_by_id: int) -> bool:
        """Mark task as blocked by another task."""
        task = self.get(task_id)
        if not task:
            return False
        deps = task.get("blocked_by", [])
        if blocked_by_id not in deps:
            deps.append(blocked_by_id)
            return self.update(task_id, blocked_by=deps, status=TaskStatus.BLOCKED)
        return True

    def remove_dependency(self, task_id: int, blocked_by_id: int) -> bool:
        """Remove a dependency."""
        task = self.get(task_id)
        if not task:
            return False
        deps = task.get("blocked_by", [])
        if blocked_by_id in deps:
            deps.remove(blocked_by_id)
            new_status = TaskStatus.PENDING if not deps else TaskStatus.BLOCKED
            return self.update(task_id, blocked_by=deps, status=new_status)
        return True

    def get_blocking_tasks(self, task_id: int) -> list[dict]:
        """Get tasks that block this task."""
        task = self.get(task_id)
        if not task:
            return []
        return [self.get(bid) for bid in task.get("blocked_by", []) if self.get(bid)]

    def check_dependencies(self, task_id: int) -> bool:
        """Check if all dependencies are completed. Updates status if unblocked."""
        task = self.get(task_id)
        if not task or task["status"] != "blocked":
            return True
        blockers = self.get_blocking_tasks(task_id)
        all_done = all(b["status"] == "completed" for b in blockers)
        if all_done:
            self.update(task_id, status=TaskStatus.PENDING, blocked_by=[])
        return all_done

    # === Tags ===
    def add_tag(self, task_id: int, tag: str) -> bool:
        """Add a tag to a task."""
        task = self.get(task_id)
        if not task:
            return False
        tags = task.get("tags", [])
        if tag not in tags:
            tags.append(tag)
            return self.update(task_id, tags=tags)
        return True

    def remove_tag(self, task_id: int, tag: str) -> bool:
        """Remove a tag from a task."""
        task = self.get(task_id)
        if not task:
            return False
        tags = task.get("tags", [])
        if tag in tags:
            tags.remove(tag)
            return self.update(task_id, tags=tags)
        return True

    def get_all_tags(self) -> list[str]:
        """Get all unique tags across tasks."""
        rows = self.db.fetchall(f"SELECT DISTINCT tags FROM {self.TABLE_NAME}")
        all_tags = set()
        for row in rows:
            tags = json.loads(row["tags"] or "[]")
            all_tags.update(tags)
        return sorted(all_tags)

    # === GTD Views ===
    def get_today(self) -> list[dict]:
        """Get tasks due or scheduled for today."""
        today = date.today().isoformat()
        sql = f"""SELECT * FROM {self.TABLE_NAME}
                  WHERE (due_date = ? OR scheduled_date = ?) AND status NOT IN ('completed', 'cancelled', 'someday')
                  ORDER BY priority DESC"""
        rows = self.db.fetchall(sql, (today, today))
        return [self._parse_task(row) for row in rows]

    def get_upcoming(self, days: int = 7) -> list[dict]:
        """Get tasks due in the next N days."""
        today = date.today()
        end = (today + timedelta(days=days)).isoformat()
        sql = f"""SELECT * FROM {self.TABLE_NAME}
                  WHERE due_date BETWEEN ? AND ? AND status NOT IN ('completed', 'cancelled', 'someday')
                  ORDER BY due_date ASC, priority DESC"""
        rows = self.db.fetchall(sql, (today.isoformat(), end))
        return [self._parse_task(row) for row in rows]

    def get_someday(self) -> list[dict]:
        """Get tasks marked as someday/maybe."""
        return self.list(status="someday", limit=1000)

    def get_overdue(self) -> list[dict]:
        """Get overdue tasks."""
        today = date.today().isoformat()
        sql = f"""SELECT * FROM {self.TABLE_NAME}
                  WHERE due_date < ? AND status NOT IN ('completed', 'cancelled')
                  ORDER BY due_date ASC"""
        rows = self.db.fetchall(sql, (today,))
        return [self._parse_task(row) for row in rows]

    def get_blocked(self) -> list[dict]:
        """Get blocked tasks."""
        return self.list(status="blocked", limit=1000)

    def get_by_context(self, context: str) -> list[dict]:
        """Get tasks by context (e.g., @home, @work, @errands)."""
        sql = f"""SELECT * FROM {self.TABLE_NAME}
                  WHERE context = ? AND status NOT IN ('completed', 'cancelled')
                  ORDER BY priority DESC"""
        rows = self.db.fetchall(sql, (context,))
        return [self._parse_task(row) for row in rows]

    def get_by_energy(self, energy_level: str) -> list[dict]:
        """Get tasks by energy level (low, medium, high)."""
        sql = f"""SELECT * FROM {self.TABLE_NAME}
                  WHERE energy_level = ? AND status NOT IN ('completed', 'cancelled')
                  ORDER BY priority DESC"""
        rows = self.db.fetchall(sql, (energy_level,))
        return [self._parse_task(row) for row in rows]

    # === Link to Goals ===
    def link_to_goal(self, task_id: int, goal_id: int) -> bool:
        """Link a task to a goal."""
        return self.update(task_id, goal_id=goal_id)

    def get_tasks_for_goal(self, goal_id: int) -> list[dict]:
        """Get all tasks linked to a goal."""
        return self.list(goal_id=goal_id, limit=1000)

    # === Statistics ===
    def get_stats(self) -> dict:
        """Get task statistics."""
        total = self.db.fetchone(f"SELECT COUNT(*) as c FROM {self.TABLE_NAME}")["c"]
        completed = self.db.fetchone(f"SELECT COUNT(*) as c FROM {self.TABLE_NAME} WHERE status='completed'")["c"]
        pending = self.db.fetchone(f"SELECT COUNT(*) as c FROM {self.TABLE_NAME} WHERE status='pending'")["c"]
        overdue = len(self.get_overdue())
        today = len(self.get_today())

        return {
            "total": total, "completed": completed, "pending": pending,
            "overdue": overdue, "due_today": today,
            "completion_rate": round(completed / total * 100, 1) if total > 0 else 0,
        }

    # === Backward Compatibility ===
    def delete(self, task_id: int) -> bool:
        return self.db.delete(self.TABLE_NAME, "id = ?", (task_id,)) > 0

    def search(self, query: str) -> list[dict]:
        pattern = f"%{query}%"
        rows = self.db.fetchall(
            f"SELECT * FROM {self.TABLE_NAME} WHERE title LIKE ? OR description LIKE ?",
            (pattern, pattern))
        return [self._parse_task(row) for row in rows]

    def count(self, status: Optional[TaskStatus] = None) -> int:
        if status:
            row = self.db.fetchone(f"SELECT COUNT(*) as c FROM {self.TABLE_NAME} WHERE status=?", (status.value,))
        else:
            row = self.db.fetchone(f"SELECT COUNT(*) as c FROM {self.TABLE_NAME}")
        return row["c"] if row else 0

    def get_due_today(self) -> list[dict]:
        return self.get_today()

    def get_categories(self) -> list[str]:
        return self.get_all_tags()
