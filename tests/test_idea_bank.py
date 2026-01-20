"""
Tests for the Content Idea Bank (CON-004).

Tests the Ideas-as-projection pattern: state derived from events only.
"""

import pytest
from pathlib import Path

from modules.core.database import Database
from modules.core.event_store import EventStore
from modules.content.idea_bank import (
    IdeaBank,
    Platform,
    IdeaStatus,
    IDEA_CREATED,
    IDEA_UPDATED,
    IDEA_STATUS_CHANGED,
    IDEA_PRIORITIZED,
)


@pytest.fixture
def idea_bank(temp_db):
    """Create an idea bank with a temporary database."""
    event_store = EventStore(db=temp_db)
    return IdeaBank(db=temp_db, event_store=event_store)


class TestIdeaAdd:
    """Tests for idea creation."""

    def test_add_returns_idea_id(self, idea_bank):
        """add() should return the idea ID."""
        idea_id = idea_bank.add("Video about Python")
        assert idea_id == 1

    def test_add_multiple_ideas(self, idea_bank):
        """add() should return incrementing IDs."""
        id1 = idea_bank.add("Idea 1")
        id2 = idea_bank.add("Idea 2")
        id3 = idea_bank.add("Idea 3")

        assert id1 == 1
        assert id2 == 2
        assert id3 == 3

    def test_add_emits_event(self, idea_bank):
        """add() should emit an IDEA_CREATED event."""
        idea_id = idea_bank.add(
            "Python Tutorial",
            "Beginner's guide",
            Platform.YOUTUBE,
            priority=1
        )

        events = idea_bank.explain(idea_id)
        assert len(events) == 1

        event = events[0]
        assert event["event_type"] == IDEA_CREATED
        assert event["payload"]["title"] == "Python Tutorial"
        assert event["payload"]["platform"] == "youtube"
        assert event["payload"]["priority"] == 1

    def test_add_with_platform(self, idea_bank):
        """add() should store platform correctly."""
        idea_id = idea_bank.add("Podcast Episode", platform=Platform.PODCAST)
        idea = idea_bank.get(idea_id)

        assert idea["platform"] == "podcast"

    def test_add_clamps_priority(self, idea_bank):
        """add() should clamp priority to 1-5."""
        id1 = idea_bank.add("Low", priority=0)
        id2 = idea_bank.add("High", priority=10)

        assert idea_bank.get(id1)["priority"] == 1
        assert idea_bank.get(id2)["priority"] == 5


class TestIdeaProjection:
    """Tests for idea state projection from events."""

    def test_get_idea_projects_state(self, idea_bank):
        """get() should project idea state from events."""
        idea_id = idea_bank.add("Test Idea", "Description", Platform.BLOG)

        idea = idea_bank.get(idea_id)
        assert idea["id"] == idea_id
        assert idea["title"] == "Test Idea"
        assert idea["description"] == "Description"
        assert idea["platform"] == "blog"
        assert idea["status"] == "draft"

    def test_get_nonexistent_idea(self, idea_bank):
        """get() should return None for nonexistent idea."""
        idea = idea_bank.get(999)
        assert idea is None

    def test_update_title_updates_projection(self, idea_bank):
        """update() should update the projected title."""
        idea_id = idea_bank.add("Original Title")
        idea_bank.update(idea_id, title="New Title")

        idea = idea_bank.get(idea_id)
        assert idea["title"] == "New Title"

    def test_update_platform_updates_projection(self, idea_bank):
        """update() should update the projected platform."""
        idea_id = idea_bank.add("Idea", platform=Platform.YOUTUBE)
        idea_bank.update(idea_id, platform=Platform.PODCAST)

        idea = idea_bank.get(idea_id)
        assert idea["platform"] == "podcast"


class TestIdeaStatus:
    """Tests for idea status changes."""

    def test_set_status_updates_projection(self, idea_bank):
        """set_status() should update the projected status."""
        idea_id = idea_bank.add("Idea")
        idea_bank.set_status(idea_id, IdeaStatus.PLANNED)

        idea = idea_bank.get(idea_id)
        assert idea["status"] == "planned"

    def test_status_workflow(self, idea_bank):
        """Ideas should transition through status workflow."""
        idea_id = idea_bank.add("Idea")

        idea_bank.set_status(idea_id, IdeaStatus.PLANNED)
        assert idea_bank.get(idea_id)["status"] == "planned"

        idea_bank.set_status(idea_id, IdeaStatus.IN_PROGRESS)
        assert idea_bank.get(idea_id)["status"] == "in_progress"

        idea_bank.set_status(idea_id, IdeaStatus.PUBLISHED)
        assert idea_bank.get(idea_id)["status"] == "published"

    def test_set_status_nonexistent_returns_false(self, idea_bank):
        """set_status() should return False for nonexistent idea."""
        result = idea_bank.set_status(999, IdeaStatus.PLANNED)
        assert result is False


class TestIdeaPriority:
    """Tests for idea prioritization."""

    def test_prioritize_updates_projection(self, idea_bank):
        """prioritize() should update the projected priority."""
        idea_id = idea_bank.add("Idea", priority=3)
        idea_bank.prioritize(idea_id, 1)

        idea = idea_bank.get(idea_id)
        assert idea["priority"] == 1

    def test_prioritize_clamps_value(self, idea_bank):
        """prioritize() should clamp priority to 1-5."""
        idea_id = idea_bank.add("Idea")

        idea_bank.prioritize(idea_id, 0)
        assert idea_bank.get(idea_id)["priority"] == 1

        idea_bank.prioritize(idea_id, 10)
        assert idea_bank.get(idea_id)["priority"] == 5

    def test_prioritize_archived_returns_false(self, idea_bank):
        """prioritize() should return False for archived idea."""
        idea_id = idea_bank.add("Idea")
        idea_bank.set_status(idea_id, IdeaStatus.ARCHIVED)

        result = idea_bank.prioritize(idea_id, 1)
        assert result is False


class TestIdeaList:
    """Tests for listing ideas."""

    def test_list_all_ideas(self, idea_bank):
        """list_ideas() should return all non-archived ideas."""
        idea_bank.add("Idea 1")
        idea_bank.add("Idea 2")
        idea_bank.add("Idea 3")

        ideas = idea_bank.list_ideas()
        assert len(ideas) == 3

    def test_list_excludes_archived_by_default(self, idea_bank):
        """list_ideas() should exclude archived ideas by default."""
        id1 = idea_bank.add("Idea 1")
        idea_bank.add("Idea 2")
        idea_bank.set_status(id1, IdeaStatus.ARCHIVED)

        ideas = idea_bank.list_ideas()
        assert len(ideas) == 1
        assert ideas[0]["title"] == "Idea 2"

    def test_list_includes_archived_when_requested(self, idea_bank):
        """list_ideas(include_archived=True) should include archived."""
        id1 = idea_bank.add("Idea 1")
        idea_bank.add("Idea 2")
        idea_bank.set_status(id1, IdeaStatus.ARCHIVED)

        ideas = idea_bank.list_ideas(include_archived=True)
        assert len(ideas) == 2

    def test_list_filter_by_platform(self, idea_bank):
        """list_ideas(platform=X) should filter by platform."""
        idea_bank.add("Video", platform=Platform.YOUTUBE)
        idea_bank.add("Podcast", platform=Platform.PODCAST)
        idea_bank.add("Another Video", platform=Platform.YOUTUBE)

        ideas = idea_bank.list_ideas(platform=Platform.YOUTUBE)
        assert len(ideas) == 2
        assert all(i["platform"] == "youtube" for i in ideas)

    def test_list_filter_by_status(self, idea_bank):
        """list_ideas(status=X) should filter by status."""
        id1 = idea_bank.add("Idea 1")
        id2 = idea_bank.add("Idea 2")
        idea_bank.add("Idea 3")
        idea_bank.set_status(id1, IdeaStatus.PLANNED)
        idea_bank.set_status(id2, IdeaStatus.PLANNED)

        ideas = idea_bank.list_ideas(status=IdeaStatus.PLANNED)
        assert len(ideas) == 2

    def test_list_sorted_by_priority(self, idea_bank):
        """list_ideas() should sort by priority (1=highest first)."""
        idea_bank.add("Low Priority", priority=5)
        idea_bank.add("High Priority", priority=1)
        idea_bank.add("Medium Priority", priority=3)

        ideas = idea_bank.list_ideas()
        priorities = [i["priority"] for i in ideas]
        assert priorities == [1, 3, 5]

    def test_list_empty(self, idea_bank):
        """list_ideas() should return empty list when no ideas."""
        ideas = idea_bank.list_ideas()
        assert ideas == []


class TestIdeaExplain:
    """Tests for idea event history (audit trail)."""

    def test_explain_returns_all_events(self, idea_bank):
        """explain() should return all events for an idea."""
        idea_id = idea_bank.add("Idea")
        idea_bank.update(idea_id, title="Updated Idea")
        idea_bank.set_status(idea_id, IdeaStatus.PLANNED)
        idea_bank.prioritize(idea_id, 1)

        events = idea_bank.explain(idea_id)
        assert len(events) == 4

        assert events[0]["event_type"] == IDEA_CREATED
        assert events[1]["event_type"] == IDEA_UPDATED
        assert events[2]["event_type"] == IDEA_STATUS_CHANGED
        assert events[3]["event_type"] == IDEA_PRIORITIZED

    def test_explain_empty_for_nonexistent(self, idea_bank):
        """explain() should return empty list for nonexistent idea."""
        events = idea_bank.explain(999)
        assert events == []


class TestEventSpineInvariant:
    """Tests verifying the Event Spine invariant is maintained."""

    def test_events_are_canonical(self, temp_db):
        """Events table should be the only source of truth."""
        event_store = EventStore(db=temp_db)
        bank1 = IdeaBank(db=temp_db, event_store=event_store)

        # Create and update with bank1
        idea_id = bank1.add("Test Idea", platform=Platform.YOUTUBE)
        bank1.update(idea_id, description="Updated")
        bank1.set_status(idea_id, IdeaStatus.PLANNED)
        bank1.prioritize(idea_id, 1)

        # Create new bank instance (simulates restart)
        bank2 = IdeaBank(db=temp_db, event_store=event_store)

        # Should project same state from events
        idea = bank2.get(idea_id)
        assert idea["title"] == "Test Idea"
        assert idea["description"] == "Updated"
        assert idea["platform"] == "youtube"
        assert idea["status"] == "planned"
        assert idea["priority"] == 1
