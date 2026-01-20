"""
Atlas Personal OS - Podcast Episode Scheduler (CON-002)

Event-sourced podcast scheduling following the Event Spine invariant.
State is derived entirely from events - no direct table mutations.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from enum import Enum

from modules.core.database import Database, get_database
from modules.core.event_store import EventStore, get_event_store


# Event types
EPISODE_PLANNED = "EPISODE_PLANNED"
EPISODE_UPDATED = "EPISODE_UPDATED"
EPISODE_OUTLINED = "EPISODE_OUTLINED"
EPISODE_RECORDED = "EPISODE_RECORDED"
EPISODE_EDITED = "EPISODE_EDITED"
EPISODE_PUBLISHED = "EPISODE_PUBLISHED"


class EpisodeStatus(Enum):
    """Episode production status."""
    PLANNED = "planned"
    OUTLINED = "outlined"
    RECORDED = "recorded"
    EDITED = "edited"
    PUBLISHED = "published"


class PodcastScheduler:
    """Podcast episode scheduling system using event sourcing."""

    ENTITY_TYPE = "episode"

    def __init__(self, db: Optional[Database] = None, event_store: Optional[EventStore] = None):
        """Initialize podcast scheduler."""
        self.db = db or get_database()
        self.event_store = event_store or get_event_store()

    def plan(
        self,
        title: str,
        description: str = "",
        guest: str = "",
        episode_number: Optional[int] = None,
        idea_id: Optional[int] = None,
        duration_estimate: Optional[int] = None,
        tags: str = ""
    ) -> int:
        """
        Plan a new podcast episode.

        Args:
            title: Episode title
            description: Episode description
            guest: Guest name (if any)
            episode_number: Episode number in series
            idea_id: Optional link to idea_bank
            duration_estimate: Estimated duration in minutes
            tags: Comma-separated tags

        Returns:
            Episode ID
        """
        episode_id = self._get_next_id()

        # Auto-assign episode number if not provided
        if episode_number is None:
            episode_number = episode_id

        self.event_store.emit(
            event_type=EPISODE_PLANNED,
            entity_type=self.ENTITY_TYPE,
            entity_id=episode_id,
            payload={
                "title": title,
                "description": description,
                "guest": guest,
                "episode_number": episode_number,
                "idea_id": idea_id,
                "duration_estimate": duration_estimate,
                "tags": tags,
                "status": EpisodeStatus.PLANNED.value,
            }
        )
        return episode_id

    def _get_next_id(self) -> int:
        """Get the next available episode ID."""
        events = self.event_store.query(
            entity_type=self.ENTITY_TYPE,
            event_type=EPISODE_PLANNED
        )
        if not events:
            return 1
        max_id = max(int(e["entity_id"]) for e in events)
        return max_id + 1

    def get(self, episode_id: int) -> Optional[dict]:
        """Get episode state by projecting from events."""
        events = self.event_store.query(
            entity_type=self.ENTITY_TYPE,
            entity_id=episode_id
        )
        if not events:
            return None
        return self._project(events)

    def _project(self, events: list[dict]) -> dict:
        """Project episode state from events."""
        state = {
            "id": None,
            "title": "",
            "description": "",
            "guest": "",
            "episode_number": None,
            "idea_id": None,
            "duration_estimate": None,
            "tags": "",
            "status": EpisodeStatus.PLANNED.value,
            "outlined_at": None,
            "recorded_at": None,
            "edited_at": None,
            "published_at": None,
            "audio_url": None,
        }

        for event in events:
            payload = event["payload"]
            if isinstance(payload, str):
                import json
                payload = json.loads(payload)

            state["id"] = int(event["entity_id"])

            if event["event_type"] == EPISODE_PLANNED:
                state.update({
                    "title": payload.get("title", ""),
                    "description": payload.get("description", ""),
                    "guest": payload.get("guest", ""),
                    "episode_number": payload.get("episode_number"),
                    "idea_id": payload.get("idea_id"),
                    "duration_estimate": payload.get("duration_estimate"),
                    "tags": payload.get("tags", ""),
                    "status": payload.get("status", EpisodeStatus.PLANNED.value),
                })
            elif event["event_type"] == EPISODE_UPDATED:
                for key in ["title", "description", "guest", "episode_number", "duration_estimate", "tags"]:
                    if key in payload:
                        state[key] = payload[key]
            elif event["event_type"] == EPISODE_OUTLINED:
                state["status"] = EpisodeStatus.OUTLINED.value
                state["outlined_at"] = payload.get("outlined_at")
            elif event["event_type"] == EPISODE_RECORDED:
                state["status"] = EpisodeStatus.RECORDED.value
                state["recorded_at"] = payload.get("recorded_at")
            elif event["event_type"] == EPISODE_EDITED:
                state["status"] = EpisodeStatus.EDITED.value
                state["edited_at"] = payload.get("edited_at")
            elif event["event_type"] == EPISODE_PUBLISHED:
                state["status"] = EpisodeStatus.PUBLISHED.value
                state["published_at"] = payload.get("published_at")
                state["audio_url"] = payload.get("audio_url")

        return state

    def update(self, episode_id: int, **kwargs) -> bool:
        """Update episode details."""
        episode = self.get(episode_id)
        if not episode:
            return False

        allowed = ["title", "description", "guest", "episode_number", "duration_estimate", "tags"]
        updates = {k: v for k, v in kwargs.items() if k in allowed and v is not None}

        if not updates:
            return False

        self.event_store.emit(
            event_type=EPISODE_UPDATED,
            entity_type=self.ENTITY_TYPE,
            entity_id=episode_id,
            payload=updates
        )
        return True

    def mark_outlined(self, episode_id: int) -> bool:
        """Mark episode outline as completed."""
        episode = self.get(episode_id)
        if not episode or episode["status"] != EpisodeStatus.PLANNED.value:
            return False

        self.event_store.emit(
            event_type=EPISODE_OUTLINED,
            entity_type=self.ENTITY_TYPE,
            entity_id=episode_id,
            payload={"outlined_at": datetime.now().isoformat()}
        )
        return True

    def mark_recorded(self, episode_id: int) -> bool:
        """Mark episode as recorded."""
        episode = self.get(episode_id)
        if not episode or episode["status"] != EpisodeStatus.OUTLINED.value:
            return False

        self.event_store.emit(
            event_type=EPISODE_RECORDED,
            entity_type=self.ENTITY_TYPE,
            entity_id=episode_id,
            payload={"recorded_at": datetime.now().isoformat()}
        )
        return True

    def mark_edited(self, episode_id: int) -> bool:
        """Mark episode as edited."""
        episode = self.get(episode_id)
        if not episode or episode["status"] != EpisodeStatus.RECORDED.value:
            return False

        self.event_store.emit(
            event_type=EPISODE_EDITED,
            entity_type=self.ENTITY_TYPE,
            entity_id=episode_id,
            payload={"edited_at": datetime.now().isoformat()}
        )
        return True

    def mark_published(self, episode_id: int, audio_url: str = "") -> bool:
        """Mark episode as published."""
        episode = self.get(episode_id)
        if not episode or episode["status"] != EpisodeStatus.EDITED.value:
            return False

        self.event_store.emit(
            event_type=EPISODE_PUBLISHED,
            entity_type=self.ENTITY_TYPE,
            entity_id=episode_id,
            payload={
                "published_at": datetime.now().isoformat(),
                "audio_url": audio_url,
            }
        )
        return True

    def list_episodes(
        self,
        status: Optional[EpisodeStatus] = None,
        guest: Optional[str] = None,
        limit: int = 100
    ) -> list[dict]:
        """List all episodes, optionally filtered."""
        events = self.event_store.query(
            entity_type=self.ENTITY_TYPE,
            event_type=EPISODE_PLANNED
        )

        episode_ids = sorted(set(int(e["entity_id"]) for e in events))
        episodes = []

        for eid in episode_ids:
            episode = self.get(eid)
            if episode:
                if status and episode["status"] != status.value:
                    continue
                if guest and guest.lower() not in episode["guest"].lower():
                    continue
                episodes.append(episode)

        return episodes[:limit]

    def explain(self, episode_id: int) -> list[dict]:
        """Get event history for an episode (audit trail)."""
        return self.event_store.query(
            entity_type=self.ENTITY_TYPE,
            entity_id=episode_id
        )
