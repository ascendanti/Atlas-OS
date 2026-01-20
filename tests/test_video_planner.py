"""
Tests for the YouTube Video Planner (CON-001).

Tests the Video-as-projection pattern: state derived from events only.
"""

import pytest
from pathlib import Path

from modules.core.database import Database
from modules.core.event_store import EventStore
from modules.content.video_planner import (
    VideoPlanner,
    VideoStatus,
    VIDEO_PLANNED,
    VIDEO_UPDATED,
    VIDEO_SCRIPTED,
    VIDEO_RECORDED,
    VIDEO_EDITED,
    VIDEO_PUBLISHED,
)


@pytest.fixture
def video_planner(temp_db):
    """Create a video planner with a temporary database."""
    event_store = EventStore(db=temp_db)
    return VideoPlanner(db=temp_db, event_store=event_store)


class TestVideoPlan:
    """Tests for video creation."""

    def test_plan_returns_video_id(self, video_planner):
        """plan() should return the video ID."""
        video_id = video_planner.plan("Python Tutorial")
        assert video_id == 1

    def test_plan_multiple_videos(self, video_planner):
        """plan() should return incrementing IDs."""
        id1 = video_planner.plan("Video 1")
        id2 = video_planner.plan("Video 2")
        id3 = video_planner.plan("Video 3")

        assert id1 == 1
        assert id2 == 2
        assert id3 == 3

    def test_plan_emits_event(self, video_planner):
        """plan() should emit a VIDEO_PLANNED event."""
        video_id = video_planner.plan(
            "Python Tutorial",
            "Beginner's guide",
            idea_id=5,
            duration_estimate=15,
            tags="python,tutorial"
        )

        events = video_planner.explain(video_id)
        assert len(events) == 1

        event = events[0]
        assert event["event_type"] == VIDEO_PLANNED
        assert event["payload"]["title"] == "Python Tutorial"
        assert event["payload"]["idea_id"] == 5
        assert event["payload"]["duration_estimate"] == 15

    def test_plan_with_defaults(self, video_planner):
        """plan() should use default values."""
        video_id = video_planner.plan("Simple Video")
        video = video_planner.get(video_id)

        assert video["status"] == "planned"
        assert video["description"] == ""
        assert video["idea_id"] is None


class TestVideoProjection:
    """Tests for video state projection from events."""

    def test_get_video_projects_state(self, video_planner):
        """get() should project video state from events."""
        video_id = video_planner.plan("Test Video", "Description", tags="test")

        video = video_planner.get(video_id)
        assert video["id"] == video_id
        assert video["title"] == "Test Video"
        assert video["description"] == "Description"
        assert video["tags"] == "test"
        assert video["status"] == "planned"

    def test_get_nonexistent_video(self, video_planner):
        """get() should return None for nonexistent video."""
        video = video_planner.get(999)
        assert video is None

    def test_update_title_updates_projection(self, video_planner):
        """update() should update the projected title."""
        video_id = video_planner.plan("Original Title")
        video_planner.update(video_id, title="New Title")

        video = video_planner.get(video_id)
        assert video["title"] == "New Title"

    def test_update_multiple_fields(self, video_planner):
        """update() should update multiple fields."""
        video_id = video_planner.plan("Video", duration_estimate=10)
        video_planner.update(video_id, description="Updated", duration_estimate=20)

        video = video_planner.get(video_id)
        assert video["description"] == "Updated"
        assert video["duration_estimate"] == 20


class TestVideoWorkflow:
    """Tests for video production workflow."""

    def test_workflow_planned_to_scripted(self, video_planner):
        """mark_scripted() should transition from planned to scripted."""
        video_id = video_planner.plan("Video")
        result = video_planner.mark_scripted(video_id)

        assert result is True
        video = video_planner.get(video_id)
        assert video["status"] == "scripted"
        assert video["script_completed_at"] is not None

    def test_workflow_scripted_to_recorded(self, video_planner):
        """mark_recorded() should transition from scripted to recorded."""
        video_id = video_planner.plan("Video")
        video_planner.mark_scripted(video_id)
        result = video_planner.mark_recorded(video_id)

        assert result is True
        video = video_planner.get(video_id)
        assert video["status"] == "recorded"
        assert video["recorded_at"] is not None

    def test_workflow_recorded_to_edited(self, video_planner):
        """mark_edited() should transition from recorded to edited."""
        video_id = video_planner.plan("Video")
        video_planner.mark_scripted(video_id)
        video_planner.mark_recorded(video_id)
        result = video_planner.mark_edited(video_id)

        assert result is True
        video = video_planner.get(video_id)
        assert video["status"] == "edited"
        assert video["edited_at"] is not None

    def test_workflow_edited_to_published(self, video_planner):
        """mark_published() should transition from edited to published."""
        video_id = video_planner.plan("Video")
        video_planner.mark_scripted(video_id)
        video_planner.mark_recorded(video_id)
        video_planner.mark_edited(video_id)
        result = video_planner.mark_published(video_id, url="https://youtube.com/v/123")

        assert result is True
        video = video_planner.get(video_id)
        assert video["status"] == "published"
        assert video["published_at"] is not None
        assert video["publish_url"] == "https://youtube.com/v/123"

    def test_full_workflow(self, video_planner):
        """Video should transition through full workflow."""
        video_id = video_planner.plan("Tutorial Video", duration_estimate=20)

        assert video_planner.get(video_id)["status"] == "planned"

        video_planner.mark_scripted(video_id)
        assert video_planner.get(video_id)["status"] == "scripted"

        video_planner.mark_recorded(video_id)
        assert video_planner.get(video_id)["status"] == "recorded"

        video_planner.mark_edited(video_id)
        assert video_planner.get(video_id)["status"] == "edited"

        video_planner.mark_published(video_id, "https://youtube.com/watch?v=abc")
        assert video_planner.get(video_id)["status"] == "published"

    def test_cannot_skip_workflow_steps(self, video_planner):
        """Workflow should not allow skipping steps."""
        video_id = video_planner.plan("Video")

        # Cannot go directly to recorded without scripted
        assert video_planner.mark_recorded(video_id) is False
        assert video_planner.get(video_id)["status"] == "planned"

        # Cannot go directly to edited
        assert video_planner.mark_edited(video_id) is False

        # Cannot go directly to published
        assert video_planner.mark_published(video_id) is False

    def test_nonexistent_video_workflow(self, video_planner):
        """Workflow methods should return False for nonexistent video."""
        assert video_planner.mark_scripted(999) is False
        assert video_planner.mark_recorded(999) is False
        assert video_planner.mark_edited(999) is False
        assert video_planner.mark_published(999) is False


class TestVideoList:
    """Tests for listing videos."""

    def test_list_all_videos(self, video_planner):
        """list_videos() should return all videos."""
        video_planner.plan("Video 1")
        video_planner.plan("Video 2")
        video_planner.plan("Video 3")

        videos = video_planner.list_videos()
        assert len(videos) == 3

    def test_list_filter_by_status(self, video_planner):
        """list_videos(status=X) should filter by status."""
        id1 = video_planner.plan("Video 1")
        id2 = video_planner.plan("Video 2")
        video_planner.plan("Video 3")

        video_planner.mark_scripted(id1)
        video_planner.mark_scripted(id2)

        videos = video_planner.list_videos(status=VideoStatus.SCRIPTED)
        assert len(videos) == 2
        assert all(v["status"] == "scripted" for v in videos)

    def test_list_empty(self, video_planner):
        """list_videos() should return empty list when no videos."""
        videos = video_planner.list_videos()
        assert videos == []


class TestVideoExplain:
    """Tests for video event history (audit trail)."""

    def test_explain_returns_all_events(self, video_planner):
        """explain() should return all events for a video."""
        video_id = video_planner.plan("Video")
        video_planner.update(video_id, title="Updated Video")
        video_planner.mark_scripted(video_id)
        video_planner.mark_recorded(video_id)

        events = video_planner.explain(video_id)
        assert len(events) == 4

        assert events[0]["event_type"] == VIDEO_PLANNED
        assert events[1]["event_type"] == VIDEO_UPDATED
        assert events[2]["event_type"] == VIDEO_SCRIPTED
        assert events[3]["event_type"] == VIDEO_RECORDED

    def test_explain_empty_for_nonexistent(self, video_planner):
        """explain() should return empty list for nonexistent video."""
        events = video_planner.explain(999)
        assert events == []


class TestEventSpineInvariant:
    """Tests verifying the Event Spine invariant is maintained."""

    def test_events_are_canonical(self, temp_db):
        """Events table should be the only source of truth."""
        event_store = EventStore(db=temp_db)
        planner1 = VideoPlanner(db=temp_db, event_store=event_store)

        # Create and update with planner1
        video_id = planner1.plan("Test Video", duration_estimate=10)
        planner1.update(video_id, description="Updated")
        planner1.mark_scripted(video_id)

        # Create new planner instance (simulates restart)
        planner2 = VideoPlanner(db=temp_db, event_store=event_store)

        # Should project same state from events
        video = planner2.get(video_id)
        assert video["title"] == "Test Video"
        assert video["description"] == "Updated"
        assert video["status"] == "scripted"
        assert video["script_completed_at"] is not None
