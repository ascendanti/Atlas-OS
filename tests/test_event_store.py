"""
Tests for the Event Store (CORE-004).

Tests the Event Spine invariant: COMMAND → EVENT → PROJECTION → POLICY
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
import tempfile

from modules.core.database import Database
from modules.core.event_store import EventStore


@pytest.fixture
def event_store(temp_db):
    """Create an event store with a temporary database."""
    return EventStore(db=temp_db)


class TestEventEmit:
    """Tests for emit_event functionality."""

    def test_emit_returns_event_id(self, event_store):
        """emit() should return the event ID."""
        event_id = event_store.emit(
            event_type="TASK_CREATED",
            entity_type="task",
            entity_id=1,
            payload={"title": "Test task"}
        )
        assert event_id == 1

    def test_emit_multiple_events(self, event_store):
        """emit() should return incrementing IDs."""
        id1 = event_store.emit("E1", "test", 1, {"a": 1})
        id2 = event_store.emit("E2", "test", 1, {"a": 2})
        id3 = event_store.emit("E3", "test", 2, {"a": 3})

        assert id1 == 1
        assert id2 == 2
        assert id3 == 3

    def test_emit_stores_all_fields(self, event_store):
        """emit() should store all fields correctly."""
        event_store.emit(
            event_type="GOAL_DEFINED",
            entity_type="goal",
            entity_id="goal-123",
            payload={"title": "Learn Python", "target": 100}
        )

        events = event_store.query()
        assert len(events) == 1

        event = events[0]
        assert event["event_type"] == "GOAL_DEFINED"
        assert event["entity_type"] == "goal"
        assert event["entity_id"] == "goal-123"
        assert event["payload"]["title"] == "Learn Python"
        assert event["payload"]["target"] == 100


class TestEventQuery:
    """Tests for query_events functionality."""

    def test_query_all_events(self, event_store):
        """query() with no filters returns all events."""
        event_store.emit("E1", "task", 1, {})
        event_store.emit("E2", "goal", 1, {})
        event_store.emit("E3", "task", 2, {})

        events = event_store.query()
        assert len(events) == 3

    def test_query_by_entity_type(self, event_store):
        """query(entity_type=X) filters by entity type."""
        event_store.emit("CREATED", "task", 1, {})
        event_store.emit("CREATED", "goal", 1, {})
        event_store.emit("UPDATED", "task", 2, {})

        task_events = event_store.query(entity_type="task")
        assert len(task_events) == 2
        assert all(e["entity_type"] == "task" for e in task_events)

    def test_query_by_entity_id(self, event_store):
        """query(entity_id=X) filters by entity ID."""
        event_store.emit("CREATED", "task", 1, {})
        event_store.emit("UPDATED", "task", 1, {})
        event_store.emit("CREATED", "task", 2, {})

        events = event_store.query(entity_id=1)
        assert len(events) == 2
        assert all(e["entity_id"] == "1" for e in events)

    def test_query_by_event_type(self, event_store):
        """query(event_type=X) filters by event type."""
        event_store.emit("TASK_CREATED", "task", 1, {})
        event_store.emit("TASK_UPDATED", "task", 1, {})
        event_store.emit("TASK_CREATED", "task", 2, {})

        created_events = event_store.query(event_type="TASK_CREATED")
        assert len(created_events) == 2
        assert all(e["event_type"] == "TASK_CREATED" for e in created_events)

    def test_query_combined_filters(self, event_store):
        """query() with multiple filters combines them with AND."""
        event_store.emit("CREATED", "task", 1, {})
        event_store.emit("UPDATED", "task", 1, {})
        event_store.emit("CREATED", "goal", 1, {})

        events = event_store.query(entity_type="task", event_type="CREATED")
        assert len(events) == 1
        assert events[0]["entity_type"] == "task"
        assert events[0]["event_type"] == "CREATED"

    def test_query_returns_chronological_order(self, event_store):
        """query() returns events in chronological order."""
        event_store.emit("E1", "test", 1, {"order": 1})
        event_store.emit("E2", "test", 1, {"order": 2})
        event_store.emit("E3", "test", 1, {"order": 3})

        events = event_store.query()
        orders = [e["payload"]["order"] for e in events]
        assert orders == [1, 2, 3]


class TestEventExplain:
    """Tests for explain() functionality."""

    def test_explain_returns_entity_history(self, event_store):
        """explain() returns all events for an entity."""
        event_store.emit("GOAL_DEFINED", "goal", 1, {"title": "Learn Python"})
        event_store.emit("GOAL_TARGET_SET", "goal", 1, {"target_date": "2026-06-01"})
        event_store.emit("GOAL_UPDATED", "goal", 1, {"progress": 25})

        # Add events for other entities (should not appear)
        event_store.emit("GOAL_DEFINED", "goal", 2, {"title": "Other goal"})
        event_store.emit("TASK_CREATED", "task", 1, {"title": "Some task"})

        history = event_store.explain("goal", 1)
        assert len(history) == 3
        assert history[0]["event_type"] == "GOAL_DEFINED"
        assert history[1]["event_type"] == "GOAL_TARGET_SET"
        assert history[2]["event_type"] == "GOAL_UPDATED"

    def test_explain_empty_for_nonexistent_entity(self, event_store):
        """explain() returns empty list for entity with no events."""
        history = event_store.explain("goal", 999)
        assert history == []


class TestEventCount:
    """Tests for count() functionality."""

    def test_count_all_events(self, event_store):
        """count() returns total event count."""
        event_store.emit("E1", "task", 1, {})
        event_store.emit("E2", "goal", 1, {})
        event_store.emit("E3", "task", 2, {})

        assert event_store.count() == 3

    def test_count_by_entity_type(self, event_store):
        """count(entity_type=X) counts events for entity type."""
        event_store.emit("E1", "task", 1, {})
        event_store.emit("E2", "goal", 1, {})
        event_store.emit("E3", "task", 2, {})

        assert event_store.count(entity_type="task") == 2
        assert event_store.count(entity_type="goal") == 1


class TestTaskTrackerEventIntegration:
    """Tests for task_tracker emitting events."""

    def test_task_add_emits_event(self, temp_db):
        """TaskTracker.add() should emit a TASK_CREATED event."""
        from modules.life.task_tracker import TaskTracker, TaskPriority

        event_store = EventStore(db=temp_db)
        tracker = TaskTracker(db=temp_db, event_store=event_store)

        task_id = tracker.add(
            title="Test task",
            description="A test",
            priority=TaskPriority.HIGH,
            category="testing"
        )

        events = event_store.query(entity_type="task", entity_id=task_id)
        assert len(events) == 1

        event = events[0]
        assert event["event_type"] == "TASK_CREATED"
        assert event["payload"]["title"] == "Test task"
        assert event["payload"]["priority"] == TaskPriority.HIGH.value
