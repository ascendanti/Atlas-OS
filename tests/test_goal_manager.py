"""
Tests for the Goal Manager (LIFE-003).

Tests the Goals-as-projection pattern: state derived from events only.
"""

import pytest
from datetime import date, timedelta
from pathlib import Path
import tempfile

from modules.core.database import Database
from modules.core.event_store import EventStore
from modules.life.goal_manager import (
    GoalManager,
    GOAL_DEFINED,
    GOAL_TARGET_SET,
    GOAL_UPDATED,
)


@pytest.fixture
def goal_manager(temp_db):
    """Create a goal manager with a temporary database."""
    event_store = EventStore(db=temp_db)
    return GoalManager(db=temp_db, event_store=event_store)


class TestGoalDefine:
    """Tests for goal definition."""

    def test_define_returns_goal_id(self, goal_manager):
        """define() should return the goal ID."""
        goal_id = goal_manager.define("Learn Python")
        assert goal_id == 1

    def test_define_multiple_goals(self, goal_manager):
        """define() should return incrementing IDs."""
        id1 = goal_manager.define("Goal 1")
        id2 = goal_manager.define("Goal 2")
        id3 = goal_manager.define("Goal 3")

        assert id1 == 1
        assert id2 == 2
        assert id3 == 3

    def test_define_emits_event(self, goal_manager):
        """define() should emit a GOAL_DEFINED event."""
        goal_id = goal_manager.define("Learn Python", "Master the language")

        events = goal_manager.explain(goal_id)
        assert len(events) == 1

        event = events[0]
        assert event["event_type"] == GOAL_DEFINED
        assert event["payload"]["title"] == "Learn Python"
        assert event["payload"]["description"] == "Master the language"


class TestGoalProjection:
    """Tests for goal state projection from events."""

    def test_get_goal_projects_state(self, goal_manager):
        """get() should project goal state from events."""
        goal_id = goal_manager.define("Learn Python", "Master the language")

        goal = goal_manager.get(goal_id)
        assert goal["id"] == goal_id
        assert goal["title"] == "Learn Python"
        assert goal["description"] == "Master the language"
        assert goal["current_value"] == 0
        assert goal["target_value"] == 100

    def test_get_nonexistent_goal(self, goal_manager):
        """get() should return None for nonexistent goal."""
        goal = goal_manager.get(999)
        assert goal is None

    def test_set_target_updates_projection(self, goal_manager):
        """set_target() should update the projected state."""
        goal_id = goal_manager.define("Learn Python")
        target = date.today() + timedelta(days=30)

        goal_manager.set_target(goal_id, target, 100)

        goal = goal_manager.get(goal_id)
        assert goal["target_date"] == target.isoformat()
        assert goal["target_value"] == 100

    def test_update_progress_updates_projection(self, goal_manager):
        """update_progress() should update the projected state."""
        goal_id = goal_manager.define("Learn Python")

        goal_manager.update_progress(goal_id, 25, "Completed basics")

        goal = goal_manager.get(goal_id)
        assert goal["current_value"] == 25

    def test_multiple_updates_project_latest(self, goal_manager):
        """Multiple updates should project the latest value."""
        goal_id = goal_manager.define("Learn Python")

        goal_manager.update_progress(goal_id, 25)
        goal_manager.update_progress(goal_id, 50)
        goal_manager.update_progress(goal_id, 75)

        goal = goal_manager.get(goal_id)
        assert goal["current_value"] == 75


class TestGoalProgress:
    """Tests for progress calculation."""

    def test_progress_percentage(self, goal_manager):
        """progress() should calculate percentage correctly."""
        goal_id = goal_manager.define("Learn Python")
        goal_manager.set_target(goal_id, date.today() + timedelta(days=30), 100)
        goal_manager.update_progress(goal_id, 25)

        progress = goal_manager.progress(goal_id)
        assert progress["percentage"] == 25.0
        assert progress["current_value"] == 25
        assert progress["target_value"] == 100

    def test_progress_status_active(self, goal_manager):
        """progress() should show 'active' for in-progress goals."""
        goal_id = goal_manager.define("Learn Python")
        goal_manager.set_target(goal_id, date.today() + timedelta(days=30), 100)
        goal_manager.update_progress(goal_id, 25)

        progress = goal_manager.progress(goal_id)
        assert progress["status"] == "active"

    def test_progress_status_completed(self, goal_manager):
        """progress() should show 'completed' at 100%."""
        goal_id = goal_manager.define("Learn Python")
        goal_manager.set_target(goal_id, date.today() + timedelta(days=30), 100)
        goal_manager.update_progress(goal_id, 100)

        progress = goal_manager.progress(goal_id)
        assert progress["status"] == "completed"
        assert progress["percentage"] == 100.0

    def test_progress_status_overdue(self, goal_manager):
        """progress() should show 'overdue' for past due goals."""
        goal_id = goal_manager.define("Learn Python")
        goal_manager.set_target(goal_id, date.today() - timedelta(days=1), 100)
        goal_manager.update_progress(goal_id, 50)

        progress = goal_manager.progress(goal_id)
        assert progress["status"] == "overdue"
        assert progress["days_remaining"] < 0

    def test_progress_status_urgent(self, goal_manager):
        """progress() should show 'urgent' for goals due within 7 days."""
        goal_id = goal_manager.define("Learn Python")
        goal_manager.set_target(goal_id, date.today() + timedelta(days=3), 100)
        goal_manager.update_progress(goal_id, 50)

        progress = goal_manager.progress(goal_id)
        assert progress["status"] == "urgent"

    def test_progress_nonexistent_goal(self, goal_manager):
        """progress() should return None for nonexistent goal."""
        progress = goal_manager.progress(999)
        assert progress is None


class TestGoalList:
    """Tests for listing goals."""

    def test_list_all_goals(self, goal_manager):
        """list() should return all goals."""
        goal_manager.define("Goal 1")
        goal_manager.define("Goal 2")
        goal_manager.define("Goal 3")

        goals = goal_manager.list_goals()
        assert len(goals) == 3
        titles = [g["title"] for g in goals]
        assert "Goal 1" in titles
        assert "Goal 2" in titles
        assert "Goal 3" in titles

    def test_list_empty(self, goal_manager):
        """list() should return empty list when no goals."""
        goals = goal_manager.list_goals()
        assert goals == []


class TestGoalExplain:
    """Tests for goal event history (audit trail)."""

    def test_explain_returns_all_events(self, goal_manager):
        """explain() should return all events for a goal."""
        goal_id = goal_manager.define("Learn Python")
        goal_manager.set_target(goal_id, date.today() + timedelta(days=30), 100)
        goal_manager.update_progress(goal_id, 25, "Started tutorials")
        goal_manager.update_progress(goal_id, 50, "Halfway done")

        events = goal_manager.explain(goal_id)
        assert len(events) == 4

        assert events[0]["event_type"] == GOAL_DEFINED
        assert events[1]["event_type"] == GOAL_TARGET_SET
        assert events[2]["event_type"] == GOAL_UPDATED
        assert events[3]["event_type"] == GOAL_UPDATED

    def test_explain_empty_for_nonexistent(self, goal_manager):
        """explain() should return empty list for nonexistent goal."""
        events = goal_manager.explain(999)
        assert events == []


class TestEventSpineInvariant:
    """Tests verifying the Event Spine invariant is maintained."""

    def test_no_direct_state_mutation(self, goal_manager):
        """Goal state should only be derivable from events."""
        goal_id = goal_manager.define("Test Goal")

        # Get state via projection
        goal_v1 = goal_manager.get(goal_id)
        assert goal_v1["current_value"] == 0

        # Update via event
        goal_manager.update_progress(goal_id, 50)

        # Get state again - should reflect event
        goal_v2 = goal_manager.get(goal_id)
        assert goal_v2["current_value"] == 50

        # Events should be the source of truth
        events = goal_manager.explain(goal_id)
        assert len(events) == 2  # DEFINED + UPDATED

    def test_events_are_canonical(self, temp_db):
        """Events table should be the only source of truth."""
        event_store = EventStore(db=temp_db)
        manager1 = GoalManager(db=temp_db, event_store=event_store)

        # Create goal with manager1
        goal_id = manager1.define("Test Goal")
        manager1.update_progress(goal_id, 75)

        # Create new manager instance (simulates restart)
        manager2 = GoalManager(db=temp_db, event_store=event_store)

        # Should project same state from events
        goal = manager2.get(goal_id)
        assert goal["title"] == "Test Goal"
        assert goal["current_value"] == 75
