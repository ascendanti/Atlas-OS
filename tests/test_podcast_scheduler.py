"""
Tests for the Podcast Episode Scheduler (CON-002).

Tests the Episode-as-projection pattern: state derived from events only.
"""

import pytest

from modules.core.database import Database
from modules.core.event_store import EventStore
from modules.content.podcast_scheduler import (
    PodcastScheduler,
    EpisodeStatus,
    EPISODE_PLANNED,
    EPISODE_UPDATED,
    EPISODE_OUTLINED,
    EPISODE_RECORDED,
    EPISODE_EDITED,
    EPISODE_PUBLISHED,
)


@pytest.fixture
def scheduler(temp_db):
    """Create a podcast scheduler with a temporary database."""
    event_store = EventStore(db=temp_db)
    return PodcastScheduler(db=temp_db, event_store=event_store)


class TestEpisodePlan:
    """Tests for episode planning."""

    def test_plan_returns_episode_id(self, scheduler):
        """plan() should return the episode ID."""
        episode_id = scheduler.plan("My First Episode")
        assert episode_id == 1

    def test_plan_multiple_episodes(self, scheduler):
        """plan() should return incrementing IDs."""
        id1 = scheduler.plan("Episode 1")
        id2 = scheduler.plan("Episode 2")
        id3 = scheduler.plan("Episode 3")

        assert id1 == 1
        assert id2 == 2
        assert id3 == 3

    def test_plan_emits_event(self, scheduler):
        """plan() should emit an EPISODE_PLANNED event."""
        episode_id = scheduler.plan(
            "Interview with Expert",
            description="Deep dive into AI",
            guest="Dr. Smith",
            episode_number=42,
            duration_estimate=60,
            tags="ai,interview"
        )

        events = scheduler.explain(episode_id)
        assert len(events) == 1

        event = events[0]
        assert event["event_type"] == EPISODE_PLANNED
        assert event["payload"]["title"] == "Interview with Expert"
        assert event["payload"]["guest"] == "Dr. Smith"

    def test_plan_auto_assigns_episode_number(self, scheduler):
        """plan() should auto-assign episode number if not provided."""
        episode_id = scheduler.plan("Auto Episode")
        episode = scheduler.get(episode_id)

        assert episode["episode_number"] == episode_id

    def test_plan_with_all_fields(self, scheduler):
        """plan() should store all provided fields."""
        episode_id = scheduler.plan(
            "Full Episode",
            description="Complete description",
            guest="Special Guest",
            episode_number=100,
            idea_id=5,
            duration_estimate=45,
            tags="special,featured"
        )

        episode = scheduler.get(episode_id)
        assert episode["title"] == "Full Episode"
        assert episode["description"] == "Complete description"
        assert episode["guest"] == "Special Guest"
        assert episode["episode_number"] == 100
        assert episode["idea_id"] == 5
        assert episode["duration_estimate"] == 45
        assert episode["tags"] == "special,featured"


class TestEpisodeProjection:
    """Tests for episode state projection from events."""

    def test_get_episode_projects_state(self, scheduler):
        """get() should project episode state from events."""
        episode_id = scheduler.plan("Test Episode", "Description", "Guest A")

        episode = scheduler.get(episode_id)
        assert episode["id"] == episode_id
        assert episode["title"] == "Test Episode"
        assert episode["description"] == "Description"
        assert episode["guest"] == "Guest A"
        assert episode["status"] == "planned"

    def test_get_nonexistent_episode(self, scheduler):
        """get() should return None for nonexistent episode."""
        episode = scheduler.get(999)
        assert episode is None

    def test_update_title_updates_projection(self, scheduler):
        """update() should update the projected title."""
        episode_id = scheduler.plan("Original Title")
        scheduler.update(episode_id, title="New Title")

        episode = scheduler.get(episode_id)
        assert episode["title"] == "New Title"

    def test_update_multiple_fields(self, scheduler):
        """update() should update multiple fields."""
        episode_id = scheduler.plan("Episode")
        scheduler.update(episode_id, guest="New Guest", duration_estimate=90)

        episode = scheduler.get(episode_id)
        assert episode["guest"] == "New Guest"
        assert episode["duration_estimate"] == 90


class TestEpisodeWorkflow:
    """Tests for episode production workflow."""

    def test_workflow_planned_to_outlined(self, scheduler):
        """mark_outlined() should transition from planned to outlined."""
        episode_id = scheduler.plan("Episode")
        result = scheduler.mark_outlined(episode_id)

        assert result is True
        episode = scheduler.get(episode_id)
        assert episode["status"] == "outlined"
        assert episode["outlined_at"] is not None

    def test_workflow_outlined_to_recorded(self, scheduler):
        """mark_recorded() should transition from outlined to recorded."""
        episode_id = scheduler.plan("Episode")
        scheduler.mark_outlined(episode_id)
        result = scheduler.mark_recorded(episode_id)

        assert result is True
        episode = scheduler.get(episode_id)
        assert episode["status"] == "recorded"
        assert episode["recorded_at"] is not None

    def test_workflow_recorded_to_edited(self, scheduler):
        """mark_edited() should transition from recorded to edited."""
        episode_id = scheduler.plan("Episode")
        scheduler.mark_outlined(episode_id)
        scheduler.mark_recorded(episode_id)
        result = scheduler.mark_edited(episode_id)

        assert result is True
        episode = scheduler.get(episode_id)
        assert episode["status"] == "edited"
        assert episode["edited_at"] is not None

    def test_workflow_edited_to_published(self, scheduler):
        """mark_published() should transition from edited to published."""
        episode_id = scheduler.plan("Episode")
        scheduler.mark_outlined(episode_id)
        scheduler.mark_recorded(episode_id)
        scheduler.mark_edited(episode_id)
        result = scheduler.mark_published(episode_id, audio_url="https://example.com/ep1.mp3")

        assert result is True
        episode = scheduler.get(episode_id)
        assert episode["status"] == "published"
        assert episode["published_at"] is not None
        assert episode["audio_url"] == "https://example.com/ep1.mp3"

    def test_full_workflow_to_published(self, scheduler):
        """Episode should transition through full workflow."""
        episode_id = scheduler.plan("Production Episode", guest="Famous Person")

        assert scheduler.get(episode_id)["status"] == "planned"

        scheduler.mark_outlined(episode_id)
        assert scheduler.get(episode_id)["status"] == "outlined"

        scheduler.mark_recorded(episode_id)
        assert scheduler.get(episode_id)["status"] == "recorded"

        scheduler.mark_edited(episode_id)
        assert scheduler.get(episode_id)["status"] == "edited"

        scheduler.mark_published(episode_id, "https://podcast.com/ep1")
        assert scheduler.get(episode_id)["status"] == "published"

    def test_cannot_skip_workflow_steps(self, scheduler):
        """Workflow should not allow skipping steps."""
        episode_id = scheduler.plan("Episode")

        # Cannot record without outlining
        assert scheduler.mark_recorded(episode_id) is False
        assert scheduler.get(episode_id)["status"] == "planned"

        # Cannot publish without editing
        scheduler.mark_outlined(episode_id)
        scheduler.mark_recorded(episode_id)
        assert scheduler.mark_published(episode_id) is False

    def test_nonexistent_episode_workflow(self, scheduler):
        """Workflow methods should return False for nonexistent episode."""
        assert scheduler.mark_outlined(999) is False
        assert scheduler.mark_recorded(999) is False
        assert scheduler.mark_edited(999) is False
        assert scheduler.mark_published(999) is False


class TestEpisodeList:
    """Tests for listing episodes."""

    def test_list_all_episodes(self, scheduler):
        """list_episodes() should return all episodes."""
        scheduler.plan("Episode 1")
        scheduler.plan("Episode 2")
        scheduler.plan("Episode 3")

        episodes = scheduler.list_episodes()
        assert len(episodes) == 3

    def test_list_filter_by_status(self, scheduler):
        """list_episodes(status=X) should filter by status."""
        id1 = scheduler.plan("Episode 1")
        id2 = scheduler.plan("Episode 2")
        scheduler.plan("Episode 3")

        scheduler.mark_outlined(id1)
        scheduler.mark_outlined(id2)

        episodes = scheduler.list_episodes(status=EpisodeStatus.OUTLINED)
        assert len(episodes) == 2
        assert all(e["status"] == "outlined" for e in episodes)

    def test_list_filter_by_guest(self, scheduler):
        """list_episodes(guest=X) should filter by guest."""
        scheduler.plan("Episode 1", guest="Alice Smith")
        scheduler.plan("Episode 2", guest="Bob Jones")
        scheduler.plan("Episode 3", guest="Alice Brown")

        episodes = scheduler.list_episodes(guest="alice")
        assert len(episodes) == 2

    def test_list_empty(self, scheduler):
        """list_episodes() should return empty list when no episodes."""
        episodes = scheduler.list_episodes()
        assert episodes == []


class TestEpisodeExplain:
    """Tests for episode event history (audit trail)."""

    def test_explain_returns_all_events(self, scheduler):
        """explain() should return all events for an episode."""
        episode_id = scheduler.plan("Episode")
        scheduler.update(episode_id, title="Updated Episode")
        scheduler.mark_outlined(episode_id)
        scheduler.mark_recorded(episode_id)

        events = scheduler.explain(episode_id)
        assert len(events) == 4

        assert events[0]["event_type"] == EPISODE_PLANNED
        assert events[1]["event_type"] == EPISODE_UPDATED
        assert events[2]["event_type"] == EPISODE_OUTLINED
        assert events[3]["event_type"] == EPISODE_RECORDED

    def test_explain_empty_for_nonexistent(self, scheduler):
        """explain() should return empty list for nonexistent episode."""
        events = scheduler.explain(999)
        assert events == []


class TestEventSpineInvariant:
    """Tests verifying the Event Spine invariant is maintained."""

    def test_events_are_canonical(self, temp_db):
        """Events table should be the only source of truth."""
        event_store = EventStore(db=temp_db)
        scheduler1 = PodcastScheduler(db=temp_db, event_store=event_store)

        # Create and update with scheduler1
        episode_id = scheduler1.plan("Test Episode", guest="Test Guest")
        scheduler1.update(episode_id, description="New description")
        scheduler1.mark_outlined(episode_id)

        # Create new scheduler instance (simulates restart)
        scheduler2 = PodcastScheduler(db=temp_db, event_store=event_store)

        # Should project same state from events
        episode = scheduler2.get(episode_id)
        assert episode["title"] == "Test Episode"
        assert episode["guest"] == "Test Guest"
        assert episode["description"] == "New description"
        assert episode["status"] == "outlined"
        assert episode["outlined_at"] is not None
