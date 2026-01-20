"""
Tests for the Habit Tracker module.
"""

import pytest
from datetime import date, timedelta

from modules.life.habit_tracker import HabitTracker, HabitFrequency


class TestHabitTracker:
    """Tests for HabitTracker class."""

    def test_add_habit(self, temp_db):
        """Test adding a habit."""
        tracker = HabitTracker(db=temp_db)
        habit_id = tracker.add_habit("Exercise", description="Daily workout")

        assert habit_id == 1

        habit = tracker.get_habit(habit_id)
        assert habit["name"] == "Exercise"
        assert habit["description"] == "Daily workout"
        assert habit["frequency"] == "daily"

    def test_add_habit_with_frequency(self, temp_db):
        """Test adding a habit with specific frequency."""
        tracker = HabitTracker(db=temp_db)
        habit_id = tracker.add_habit("Weekend Review", frequency=HabitFrequency.WEEKENDS)

        habit = tracker.get_habit(habit_id)
        assert habit["frequency"] == "weekends"

    def test_list_habits(self, temp_db):
        """Test listing habits."""
        tracker = HabitTracker(db=temp_db)
        tracker.add_habit("Habit 1")
        tracker.add_habit("Habit 2")
        tracker.add_habit("Habit 3")

        habits = tracker.list_habits()
        assert len(habits) == 3

    def test_complete_habit(self, temp_db):
        """Test completing a habit."""
        tracker = HabitTracker(db=temp_db)
        habit_id = tracker.add_habit("Read")

        result = tracker.complete_habit(habit_id)
        assert result is True

        assert tracker.is_completed(habit_id)

    def test_complete_habit_multiple_times(self, temp_db):
        """Test completing a habit multiple times in a day."""
        tracker = HabitTracker(db=temp_db)
        habit_id = tracker.add_habit("Drink Water", target_count=8)

        tracker.complete_habit(habit_id, count=3)
        assert not tracker.is_completed(habit_id)  # Need 8

        tracker.complete_habit(habit_id, count=5)  # Total: 8
        assert tracker.is_completed(habit_id)

    def test_uncomplete_habit(self, temp_db):
        """Test removing a habit completion."""
        tracker = HabitTracker(db=temp_db)
        habit_id = tracker.add_habit("Test Habit")

        tracker.complete_habit(habit_id)
        assert tracker.is_completed(habit_id)

        tracker.uncomplete_habit(habit_id)
        assert not tracker.is_completed(habit_id)

    def test_streak_calculation(self, temp_db):
        """Test streak calculation."""
        tracker = HabitTracker(db=temp_db)
        habit_id = tracker.add_habit("Streak Test")

        today = date.today()

        # Complete for last 5 days including today
        for i in range(5):
            completion_date = today - timedelta(days=i)
            tracker.complete_habit(habit_id, completed_date=completion_date)

        streak = tracker.get_streak(habit_id)
        assert streak == 5

    def test_streak_broken(self, temp_db):
        """Test streak when there's a gap."""
        tracker = HabitTracker(db=temp_db)
        habit_id = tracker.add_habit("Gap Test")

        today = date.today()

        # Complete today and yesterday, skip day before
        tracker.complete_habit(habit_id, completed_date=today)
        tracker.complete_habit(habit_id, completed_date=today - timedelta(days=1))
        # Skip day 2
        tracker.complete_habit(habit_id, completed_date=today - timedelta(days=3))

        streak = tracker.get_streak(habit_id)
        assert streak == 2  # Only today and yesterday count

    def test_longest_streak(self, temp_db):
        """Test longest streak calculation."""
        tracker = HabitTracker(db=temp_db)
        habit_id = tracker.add_habit("Long Streak Test")

        base_date = date.today() - timedelta(days=30)

        # First streak: 5 days
        for i in range(5):
            tracker.complete_habit(habit_id, completed_date=base_date + timedelta(days=i))

        # Gap
        # Second streak: 10 days
        for i in range(10):
            tracker.complete_habit(habit_id, completed_date=base_date + timedelta(days=10 + i))

        longest = tracker.get_longest_streak(habit_id)
        assert longest == 10

    def test_completion_rate(self, temp_db):
        """Test completion rate calculation."""
        tracker = HabitTracker(db=temp_db)
        habit_id = tracker.add_habit("Rate Test")

        today = date.today()

        # Complete 15 out of 30 days
        for i in range(15):
            completion_date = today - timedelta(days=i * 2)
            tracker.complete_habit(habit_id, completed_date=completion_date)

        rate = tracker.get_completion_rate(habit_id, days=30)
        assert 0.4 <= rate <= 0.6  # Approximately 50%

    def test_today_status(self, temp_db):
        """Test getting today's status."""
        tracker = HabitTracker(db=temp_db)
        habit1 = tracker.add_habit("Done Today")
        habit2 = tracker.add_habit("Not Done")

        tracker.complete_habit(habit1)

        status = tracker.get_today_status()
        assert len(status) == 2

        done = next(h for h in status if h["id"] == habit1)
        not_done = next(h for h in status if h["id"] == habit2)

        assert done["completed_today"] is True
        assert not_done["completed_today"] is False

    def test_archive_habit(self, temp_db):
        """Test archiving a habit."""
        tracker = HabitTracker(db=temp_db)
        habit_id = tracker.add_habit("To Archive")

        tracker.archive_habit(habit_id)

        # Should not appear in active habits
        active_habits = tracker.list_habits(active_only=True)
        assert len(active_habits) == 0

        # Should appear when including archived
        all_habits = tracker.list_habits(active_only=False)
        assert len(all_habits) == 1

    def test_delete_habit(self, temp_db):
        """Test deleting a habit and its completions."""
        tracker = HabitTracker(db=temp_db)
        habit_id = tracker.add_habit("To Delete")
        tracker.complete_habit(habit_id)

        result = tracker.delete_habit(habit_id)
        assert result is True

        habit = tracker.get_habit(habit_id)
        assert habit is None

    def test_weekly_summary(self, temp_db):
        """Test weekly summary."""
        tracker = HabitTracker(db=temp_db)
        habit_id = tracker.add_habit("Weekly Test")

        today = date.today()
        # Complete for today
        tracker.complete_habit(habit_id, completed_date=today)

        summary = tracker.get_weekly_summary(habit_id)
        assert summary["habit_id"] == habit_id
        assert summary["days_completed"] >= 1
        assert "week_start" in summary
