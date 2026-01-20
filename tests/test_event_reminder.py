"""
Tests for the Event Reminder System (LIFE-004).

Tests the Reminder-as-projection pattern: state derived from events only.
"""

import pytest
from datetime import date, timedelta

from modules.core.database import Database
from modules.core.event_store import EventStore
from modules.life.event_reminder import (
    EventReminder,
    Recurrence,
    REMINDER_CREATED,
    REMINDER_UPDATED,
    REMINDER_COMPLETED,
    REMINDER_ARCHIVED,
)


@pytest.fixture
def reminder_system(temp_db):
    """Create an event reminder system with a temporary database."""
    event_store = EventStore(db=temp_db)
    return EventReminder(db=temp_db, event_store=event_store)


class TestReminderAdd:
    """Tests for adding reminders."""

    def test_add_returns_reminder_id(self, reminder_system):
        """add() should return the reminder ID."""
        reminder_id = reminder_system.add("Doctor appointment", "2026-02-15")
        assert reminder_id == 1

    def test_add_multiple_reminders(self, reminder_system):
        """add() should return incrementing IDs."""
        id1 = reminder_system.add("Event 1", "2026-02-01")
        id2 = reminder_system.add("Event 2", "2026-02-02")
        id3 = reminder_system.add("Event 3", "2026-02-03")

        assert id1 == 1
        assert id2 == 2
        assert id3 == 3

    def test_add_emits_event(self, reminder_system):
        """add() should emit a REMINDER_CREATED event."""
        reminder_id = reminder_system.add(
            "Meeting with team",
            event_date="2026-02-20",
            event_time="14:00",
            description="Weekly sync",
            reminder_minutes=60,
            recurrence=Recurrence.WEEKLY,
            tags="work,meeting"
        )

        events = reminder_system.explain(reminder_id)
        assert len(events) == 1

        event = events[0]
        assert event["event_type"] == REMINDER_CREATED
        assert event["payload"]["title"] == "Meeting with team"
        assert event["payload"]["event_time"] == "14:00"
        assert event["payload"]["recurrence"] == "weekly"

    def test_add_with_all_fields(self, reminder_system):
        """add() should store all provided fields."""
        reminder_id = reminder_system.add(
            "Birthday party",
            event_date="2026-03-15",
            event_time="18:00",
            description="John's 30th birthday",
            reminder_minutes=1440,  # 1 day
            recurrence=Recurrence.NONE,
            contact_id=5,
            tags="personal,birthday"
        )

        reminder = reminder_system.get(reminder_id)
        assert reminder["title"] == "Birthday party"
        assert reminder["event_date"] == "2026-03-15"
        assert reminder["event_time"] == "18:00"
        assert reminder["description"] == "John's 30th birthday"
        assert reminder["reminder_minutes"] == 1440
        assert reminder["recurrence"] == "none"
        assert reminder["contact_id"] == 5
        assert reminder["tags"] == "personal,birthday"


class TestReminderProjection:
    """Tests for reminder state projection from events."""

    def test_get_reminder_projects_state(self, reminder_system):
        """get() should project reminder state from events."""
        reminder_id = reminder_system.add(
            "Team standup",
            event_date="2026-02-10",
            event_time="09:00"
        )

        reminder = reminder_system.get(reminder_id)
        assert reminder["id"] == reminder_id
        assert reminder["title"] == "Team standup"
        assert reminder["event_date"] == "2026-02-10"
        assert reminder["completed"] is False
        assert reminder["archived"] is False

    def test_get_nonexistent_reminder(self, reminder_system):
        """get() should return None for nonexistent reminder."""
        reminder = reminder_system.get(999)
        assert reminder is None

    def test_update_title_updates_projection(self, reminder_system):
        """update() should update the projected title."""
        reminder_id = reminder_system.add("Old title", "2026-02-01")
        reminder_system.update(reminder_id, title="New title")

        reminder = reminder_system.get(reminder_id)
        assert reminder["title"] == "New title"

    def test_update_multiple_fields(self, reminder_system):
        """update() should update multiple fields."""
        reminder_id = reminder_system.add("Event", "2026-02-01")
        reminder_system.update(
            reminder_id,
            event_date="2026-02-15",
            event_time="10:00",
            description="Updated description"
        )

        reminder = reminder_system.get(reminder_id)
        assert reminder["event_date"] == "2026-02-15"
        assert reminder["event_time"] == "10:00"
        assert reminder["description"] == "Updated description"


class TestReminderComplete:
    """Tests for completing reminders."""

    def test_complete_marks_reminder_completed(self, reminder_system):
        """complete() should mark reminder as completed."""
        reminder_id = reminder_system.add("Task", "2026-02-01")
        result = reminder_system.complete(reminder_id)

        assert result is True
        reminder = reminder_system.get(reminder_id)
        assert reminder["completed"] is True
        assert reminder["completed_at"] is not None

    def test_cannot_complete_already_completed(self, reminder_system):
        """complete() should return False for already completed reminder."""
        reminder_id = reminder_system.add("Task", "2026-02-01")
        reminder_system.complete(reminder_id)

        result = reminder_system.complete(reminder_id)
        assert result is False

    def test_cannot_update_completed_reminder(self, reminder_system):
        """update() should return False for completed reminder."""
        reminder_id = reminder_system.add("Task", "2026-02-01")
        reminder_system.complete(reminder_id)

        result = reminder_system.update(reminder_id, title="New title")
        assert result is False


class TestReminderArchive:
    """Tests for archiving reminders."""

    def test_archive_marks_reminder_archived(self, reminder_system):
        """archive() should mark reminder as archived."""
        reminder_id = reminder_system.add("Old event", "2026-01-01")
        result = reminder_system.archive(reminder_id)

        assert result is True
        reminder = reminder_system.get(reminder_id)
        assert reminder["archived"] is True

    def test_cannot_archive_already_archived(self, reminder_system):
        """archive() should return False for already archived reminder."""
        reminder_id = reminder_system.add("Event", "2026-02-01")
        reminder_system.archive(reminder_id)

        result = reminder_system.archive(reminder_id)
        assert result is False

    def test_archive_nonexistent_returns_false(self, reminder_system):
        """archive() should return False for nonexistent reminder."""
        result = reminder_system.archive(999)
        assert result is False


class TestReminderSnooze:
    """Tests for snoozing reminders."""

    def test_snooze_records_snooze(self, reminder_system):
        """snooze() should record snooze time."""
        reminder_id = reminder_system.add("Meeting", "2026-02-01")
        result = reminder_system.snooze(reminder_id, minutes=30)

        assert result is True
        reminder = reminder_system.get(reminder_id)
        assert reminder["snoozed_at"] is not None
        assert reminder["snooze_minutes"] == 30

    def test_cannot_snooze_completed(self, reminder_system):
        """snooze() should return False for completed reminder."""
        reminder_id = reminder_system.add("Task", "2026-02-01")
        reminder_system.complete(reminder_id)

        result = reminder_system.snooze(reminder_id)
        assert result is False


class TestReminderList:
    """Tests for listing reminders."""

    def test_list_all_reminders(self, reminder_system):
        """list_reminders() should return all active reminders."""
        reminder_system.add("Event 1", "2026-02-01")
        reminder_system.add("Event 2", "2026-02-02")
        reminder_system.add("Event 3", "2026-02-03")

        reminders = reminder_system.list_reminders()
        assert len(reminders) == 3

    def test_list_excludes_completed_by_default(self, reminder_system):
        """list_reminders() should exclude completed reminders by default."""
        id1 = reminder_system.add("Event 1", "2026-02-01")
        reminder_system.add("Event 2", "2026-02-02")
        reminder_system.complete(id1)

        reminders = reminder_system.list_reminders()
        assert len(reminders) == 1

    def test_list_excludes_archived_by_default(self, reminder_system):
        """list_reminders() should exclude archived reminders by default."""
        id1 = reminder_system.add("Event 1", "2026-02-01")
        reminder_system.add("Event 2", "2026-02-02")
        reminder_system.archive(id1)

        reminders = reminder_system.list_reminders()
        assert len(reminders) == 1

    def test_list_filter_by_tag(self, reminder_system):
        """list_reminders(tag=X) should filter by tag."""
        reminder_system.add("Work meeting", "2026-02-01", tags="work")
        reminder_system.add("Doctor visit", "2026-02-02", tags="personal,health")
        reminder_system.add("Team lunch", "2026-02-03", tags="work,social")

        reminders = reminder_system.list_reminders(tag="work")
        assert len(reminders) == 2

    def test_list_filter_by_date_range(self, reminder_system):
        """list_reminders(from_date, to_date) should filter by date."""
        reminder_system.add("Event 1", "2026-02-01")
        reminder_system.add("Event 2", "2026-02-15")
        reminder_system.add("Event 3", "2026-03-01")

        reminders = reminder_system.list_reminders(from_date="2026-02-10", to_date="2026-02-28")
        assert len(reminders) == 1
        assert reminders[0]["event_date"] == "2026-02-15"

    def test_list_sorted_by_date(self, reminder_system):
        """list_reminders() should return reminders sorted by date."""
        reminder_system.add("Later", "2026-03-01")
        reminder_system.add("First", "2026-02-01")
        reminder_system.add("Middle", "2026-02-15")

        reminders = reminder_system.list_reminders()
        assert reminders[0]["title"] == "First"
        assert reminders[1]["title"] == "Middle"
        assert reminders[2]["title"] == "Later"

    def test_list_empty(self, reminder_system):
        """list_reminders() should return empty list when no reminders."""
        reminders = reminder_system.list_reminders()
        assert reminders == []


class TestReminderUpcoming:
    """Tests for upcoming reminders."""

    def test_upcoming_returns_next_week(self, reminder_system):
        """upcoming() should return reminders for next 7 days."""
        today = date.today()
        tomorrow = (today + timedelta(days=1)).isoformat()
        next_week = (today + timedelta(days=5)).isoformat()
        far_future = (today + timedelta(days=30)).isoformat()

        reminder_system.add("Tomorrow", tomorrow)
        reminder_system.add("Next week", next_week)
        reminder_system.add("Far future", far_future)

        upcoming = reminder_system.upcoming(days=7)
        assert len(upcoming) == 2


class TestReminderExplain:
    """Tests for reminder event history (audit trail)."""

    def test_explain_returns_all_events(self, reminder_system):
        """explain() should return all events for a reminder."""
        reminder_id = reminder_system.add("Event", "2026-02-01")
        reminder_system.update(reminder_id, title="Updated Event")
        reminder_system.snooze(reminder_id, minutes=10)
        reminder_system.complete(reminder_id)

        events = reminder_system.explain(reminder_id)
        assert len(events) == 4

        event_types = [e["event_type"] for e in events]
        assert REMINDER_CREATED in event_types
        assert REMINDER_UPDATED in event_types
        assert REMINDER_COMPLETED in event_types

    def test_explain_empty_for_nonexistent(self, reminder_system):
        """explain() should return empty list for nonexistent reminder."""
        events = reminder_system.explain(999)
        assert events == []


class TestEventSpineInvariant:
    """Tests verifying the Event Spine invariant is maintained."""

    def test_events_are_canonical(self, temp_db):
        """Events table should be the only source of truth."""
        event_store = EventStore(db=temp_db)
        system1 = EventReminder(db=temp_db, event_store=event_store)

        # Create and update with system1
        reminder_id = system1.add("Meeting", "2026-02-15", event_time="10:00")
        system1.update(reminder_id, title="Updated Meeting")
        system1.update(reminder_id, event_time="11:00")

        # Create new instance (simulates restart)
        system2 = EventReminder(db=temp_db, event_store=event_store)

        # Should project same state from events
        reminder = system2.get(reminder_id)
        assert reminder["title"] == "Updated Meeting"
        assert reminder["event_time"] == "11:00"
        assert reminder["event_date"] == "2026-02-15"
