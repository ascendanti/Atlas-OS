"""
Tests for the Task Tracker module.
"""

import pytest
from datetime import date, timedelta

from modules.life.task_tracker import TaskTracker, TaskStatus, TaskPriority


class TestTaskTracker:
    """Tests for TaskTracker class."""

    def test_add_task(self, temp_db):
        """Test adding a task."""
        tracker = TaskTracker(db=temp_db)
        task_id = tracker.add("Test Task", description="A test task")

        assert task_id == 1

        task = tracker.get(task_id)
        assert task["title"] == "Test Task"
        assert task["description"] == "A test task"
        assert task["status"] == "pending"

    def test_add_task_with_priority(self, temp_db):
        """Test adding a task with priority."""
        tracker = TaskTracker(db=temp_db)
        task_id = tracker.add("Urgent Task", priority=TaskPriority.URGENT)

        task = tracker.get(task_id)
        assert task["priority"] == 4  # URGENT = 4

    def test_add_task_with_due_date(self, temp_db):
        """Test adding a task with due date."""
        tracker = TaskTracker(db=temp_db)
        due = date.today() + timedelta(days=7)
        task_id = tracker.add("Future Task", due_date=due)

        task = tracker.get(task_id)
        assert task["due_date"] == due.isoformat()

    def test_list_tasks(self, temp_db):
        """Test listing tasks."""
        tracker = TaskTracker(db=temp_db)
        tracker.add("Task 1")
        tracker.add("Task 2")
        tracker.add("Task 3")

        tasks = tracker.list()
        assert len(tasks) == 3

    def test_list_tasks_by_status(self, temp_db):
        """Test filtering tasks by status."""
        tracker = TaskTracker(db=temp_db)
        task1 = tracker.add("Pending Task")
        task2 = tracker.add("Complete Task")
        tracker.complete(task2)

        pending = tracker.list(status=TaskStatus.PENDING)
        completed = tracker.list(status=TaskStatus.COMPLETED)

        assert len(pending) == 1
        assert len(completed) == 1
        assert pending[0]["title"] == "Pending Task"
        assert completed[0]["title"] == "Complete Task"

    def test_list_tasks_by_category(self, temp_db):
        """Test filtering tasks by category."""
        tracker = TaskTracker(db=temp_db)
        tracker.add("Work Task", category="work")
        tracker.add("Home Task", category="home")
        tracker.add("Another Work Task", category="work")

        work_tasks = tracker.list(category="work")
        assert len(work_tasks) == 2

    def test_complete_task(self, temp_db):
        """Test completing a task."""
        tracker = TaskTracker(db=temp_db)
        task_id = tracker.add("To Complete")

        result = tracker.complete(task_id)
        assert result is True

        task = tracker.get(task_id)
        assert task["status"] == "completed"
        assert task["completed_at"] is not None

    def test_delete_task(self, temp_db):
        """Test deleting a task."""
        tracker = TaskTracker(db=temp_db)
        task_id = tracker.add("To Delete")

        result = tracker.delete(task_id)
        assert result is True

        task = tracker.get(task_id)
        assert task is None

    def test_update_task(self, temp_db):
        """Test updating a task."""
        tracker = TaskTracker(db=temp_db)
        task_id = tracker.add("Original Title")

        tracker.update(task_id, title="Updated Title", priority=TaskPriority.HIGH)

        task = tracker.get(task_id)
        assert task["title"] == "Updated Title"
        assert task["priority"] == 3  # HIGH = 3

    def test_search_tasks(self, temp_db):
        """Test searching tasks."""
        tracker = TaskTracker(db=temp_db)
        tracker.add("Buy groceries", description="Milk, eggs, bread")
        tracker.add("Call mom")
        tracker.add("Fix the car")

        results = tracker.search("groceries")
        assert len(results) == 1
        assert results[0]["title"] == "Buy groceries"

        # Search in description
        results = tracker.search("Milk")
        assert len(results) == 1

    def test_get_overdue(self, temp_db):
        """Test getting overdue tasks."""
        tracker = TaskTracker(db=temp_db)
        yesterday = date.today() - timedelta(days=1)
        tomorrow = date.today() + timedelta(days=1)

        tracker.add("Overdue Task", due_date=yesterday)
        tracker.add("Future Task", due_date=tomorrow)

        overdue = tracker.get_overdue()
        assert len(overdue) == 1
        assert overdue[0]["title"] == "Overdue Task"

    def test_get_due_today(self, temp_db):
        """Test getting tasks due today."""
        tracker = TaskTracker(db=temp_db)
        today = date.today()
        tomorrow = date.today() + timedelta(days=1)

        tracker.add("Today Task", due_date=today)
        tracker.add("Tomorrow Task", due_date=tomorrow)

        due_today = tracker.get_due_today()
        assert len(due_today) == 1
        assert due_today[0]["title"] == "Today Task"

    def test_count_tasks(self, temp_db):
        """Test counting tasks."""
        tracker = TaskTracker(db=temp_db)
        tracker.add("Task 1")
        tracker.add("Task 2")
        task3 = tracker.add("Task 3")
        tracker.complete(task3)

        total = tracker.count()
        pending = tracker.count(TaskStatus.PENDING)
        completed = tracker.count(TaskStatus.COMPLETED)

        assert total == 3
        assert pending == 2
        assert completed == 1

    def test_get_nonexistent_task(self, temp_db):
        """Test getting a task that doesn't exist."""
        tracker = TaskTracker(db=temp_db)
        task = tracker.get(999)
        assert task is None

    def test_get_categories(self, temp_db):
        """Test getting unique categories."""
        tracker = TaskTracker(db=temp_db)
        tracker.add("Task 1", category="work")
        tracker.add("Task 2", category="home")
        tracker.add("Task 3", category="work")
        tracker.add("Task 4", category="personal")

        categories = tracker.get_categories()
        assert set(categories) == {"work", "home", "personal"}
