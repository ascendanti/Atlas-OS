"""
Atlas Personal OS - YouTube Video Planner (CON-001)

Event-sourced video planning following the Event Spine invariant.
State is derived entirely from events - no direct table mutations.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from enum import Enum

from modules.core.database import Database, get_database
from modules.core.event_store import EventStore, get_event_store


# Event types
VIDEO_PLANNED = "VIDEO_PLANNED"
VIDEO_UPDATED = "VIDEO_UPDATED"
VIDEO_SCRIPTED = "VIDEO_SCRIPTED"
VIDEO_RECORDED = "VIDEO_RECORDED"
VIDEO_EDITED = "VIDEO_EDITED"
VIDEO_PUBLISHED = "VIDEO_PUBLISHED"


class VideoStatus(Enum):
    """Video production status."""
    PLANNED = "planned"
    SCRIPTED = "scripted"
    RECORDED = "recorded"
    EDITED = "edited"
    PUBLISHED = "published"


class VideoPlanner:
    """YouTube video planning system using event sourcing."""

    ENTITY_TYPE = "video"

    def __init__(self, db: Optional[Database] = None, event_store: Optional[EventStore] = None):
        """Initialize video planner."""
        self.db = db or get_database()
        self.event_store = event_store or get_event_store()

    def plan(
        self,
        title: str,
        description: str = "",
        idea_id: Optional[int] = None,
        duration_estimate: Optional[int] = None,
        tags: str = ""
    ) -> int:
        """
        Plan a new video.

        Args:
            title: Video title
            description: Video description
            idea_id: Optional link to idea_bank
            duration_estimate: Estimated duration in minutes
            tags: Comma-separated tags

        Returns:
            Video ID
        """
        # Get next video ID from events
        video_id = self._get_next_id()

        self.event_store.emit(
            event_type=VIDEO_PLANNED,
            entity_type=self.ENTITY_TYPE,
            entity_id=video_id,
            payload={
                "title": title,
                "description": description,
                "idea_id": idea_id,
                "duration_estimate": duration_estimate,
                "tags": tags,
                "status": VideoStatus.PLANNED.value,
            }
        )
        return video_id

    def _get_next_id(self) -> int:
        """Get the next available video ID."""
        events = self.event_store.query(
            entity_type=self.ENTITY_TYPE,
            event_type=VIDEO_PLANNED
        )
        if not events:
            return 1
        max_id = max(int(e["entity_id"]) for e in events)
        return max_id + 1

    def get(self, video_id: int) -> Optional[dict]:
        """Get video state by projecting from events."""
        events = self.event_store.query(
            entity_type=self.ENTITY_TYPE,
            entity_id=video_id
        )
        if not events:
            return None
        return self._project(events)

    def _project(self, events: list[dict]) -> dict:
        """Project video state from events."""
        state = {
            "id": None,
            "title": "",
            "description": "",
            "idea_id": None,
            "duration_estimate": None,
            "tags": "",
            "status": VideoStatus.PLANNED.value,
            "script_completed_at": None,
            "recorded_at": None,
            "edited_at": None,
            "published_at": None,
            "publish_url": None,
        }

        for event in events:
            payload = event["payload"]
            if isinstance(payload, str):
                import json
                payload = json.loads(payload)

            state["id"] = int(event["entity_id"])

            if event["event_type"] == VIDEO_PLANNED:
                state.update({
                    "title": payload.get("title", ""),
                    "description": payload.get("description", ""),
                    "idea_id": payload.get("idea_id"),
                    "duration_estimate": payload.get("duration_estimate"),
                    "tags": payload.get("tags", ""),
                    "status": payload.get("status", VideoStatus.PLANNED.value),
                })
            elif event["event_type"] == VIDEO_UPDATED:
                for key in ["title", "description", "duration_estimate", "tags"]:
                    if key in payload:
                        state[key] = payload[key]
            elif event["event_type"] == VIDEO_SCRIPTED:
                state["status"] = VideoStatus.SCRIPTED.value
                state["script_completed_at"] = payload.get("completed_at")
            elif event["event_type"] == VIDEO_RECORDED:
                state["status"] = VideoStatus.RECORDED.value
                state["recorded_at"] = payload.get("recorded_at")
            elif event["event_type"] == VIDEO_EDITED:
                state["status"] = VideoStatus.EDITED.value
                state["edited_at"] = payload.get("edited_at")
            elif event["event_type"] == VIDEO_PUBLISHED:
                state["status"] = VideoStatus.PUBLISHED.value
                state["published_at"] = payload.get("published_at")
                state["publish_url"] = payload.get("url")

        return state

    def update(self, video_id: int, **kwargs) -> bool:
        """Update video details."""
        video = self.get(video_id)
        if not video:
            return False

        allowed = ["title", "description", "duration_estimate", "tags"]
        updates = {k: v for k, v in kwargs.items() if k in allowed and v is not None}

        if not updates:
            return False

        self.event_store.emit(
            event_type=VIDEO_UPDATED,
            entity_type=self.ENTITY_TYPE,
            entity_id=video_id,
            payload=updates
        )
        return True

    def mark_scripted(self, video_id: int) -> bool:
        """Mark video script as completed."""
        video = self.get(video_id)
        if not video or video["status"] != VideoStatus.PLANNED.value:
            return False

        self.event_store.emit(
            event_type=VIDEO_SCRIPTED,
            entity_type=self.ENTITY_TYPE,
            entity_id=video_id,
            payload={"completed_at": datetime.now().isoformat()}
        )
        return True

    def mark_recorded(self, video_id: int) -> bool:
        """Mark video as recorded."""
        video = self.get(video_id)
        if not video or video["status"] != VideoStatus.SCRIPTED.value:
            return False

        self.event_store.emit(
            event_type=VIDEO_RECORDED,
            entity_type=self.ENTITY_TYPE,
            entity_id=video_id,
            payload={"recorded_at": datetime.now().isoformat()}
        )
        return True

    def mark_edited(self, video_id: int) -> bool:
        """Mark video as edited."""
        video = self.get(video_id)
        if not video or video["status"] != VideoStatus.RECORDED.value:
            return False

        self.event_store.emit(
            event_type=VIDEO_EDITED,
            entity_type=self.ENTITY_TYPE,
            entity_id=video_id,
            payload={"edited_at": datetime.now().isoformat()}
        )
        return True

    def mark_published(self, video_id: int, url: str = "") -> bool:
        """Mark video as published."""
        video = self.get(video_id)
        if not video or video["status"] != VideoStatus.EDITED.value:
            return False

        self.event_store.emit(
            event_type=VIDEO_PUBLISHED,
            entity_type=self.ENTITY_TYPE,
            entity_id=video_id,
            payload={
                "published_at": datetime.now().isoformat(),
                "url": url,
            }
        )
        return True

    def list_videos(
        self,
        status: Optional[VideoStatus] = None,
        limit: int = 100
    ) -> list[dict]:
        """List all videos, optionally filtered by status."""
        events = self.event_store.query(
            entity_type=self.ENTITY_TYPE,
            event_type=VIDEO_PLANNED
        )

        video_ids = sorted(set(int(e["entity_id"]) for e in events))
        videos = []

        for vid in video_ids:
            video = self.get(vid)
            if video:
                if status is None or video["status"] == status.value:
                    videos.append(video)

        return videos[:limit]

    def explain(self, video_id: int) -> list[dict]:
        """Get event history for a video (audit trail)."""
        return self.event_store.query(
            entity_type=self.ENTITY_TYPE,
            entity_id=video_id
        )
