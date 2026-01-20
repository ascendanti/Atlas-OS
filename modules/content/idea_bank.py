"""
Atlas Personal OS - Content Idea Bank (CON-004)

Event-sourced content idea management implementing the Event Spine invariant:
COMMAND → EVENT → PROJECTION

Ideas are projections computed entirely from events.
Supports platform filtering, status tracking, and prioritization.
"""

from datetime import datetime
from typing import Optional
from enum import Enum
from modules.core.database import Database, get_database
from modules.core.event_store import EventStore, get_event_store


# Event Types
IDEA_CREATED = "IDEA_CREATED"
IDEA_UPDATED = "IDEA_UPDATED"
IDEA_STATUS_CHANGED = "IDEA_STATUS_CHANGED"
IDEA_PRIORITIZED = "IDEA_PRIORITIZED"


class Platform(Enum):
    """Content platforms."""
    YOUTUBE = "youtube"
    PODCAST = "podcast"
    BLOG = "blog"
    SOCIAL = "social"
    OTHER = "other"


class IdeaStatus(Enum):
    """Idea status values."""
    DRAFT = "draft"
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class IdeaBank:
    """
    Event-sourced content idea manager.

    All state is derived from events - no direct database mutations.
    """

    ENTITY_TYPE = "idea"

    def __init__(
        self,
        db: Optional[Database] = None,
        event_store: Optional[EventStore] = None
    ):
        """Initialize idea bank with event store."""
        self.db = db or get_database()
        self.event_store = event_store or get_event_store()
        self._next_id = self._compute_next_id()

    def _compute_next_id(self) -> int:
        """Compute next idea ID from existing events."""
        events = self.event_store.query(
            entity_type=self.ENTITY_TYPE,
            event_type=IDEA_CREATED
        )
        if not events:
            return 1
        max_id = max(int(e["entity_id"]) for e in events)
        return max_id + 1

    def add(
        self,
        title: str,
        description: str = "",
        platform: Platform = Platform.OTHER,
        priority: int = 3
    ) -> int:
        """
        Add a new content idea.

        Args:
            title: Idea title
            description: Idea description
            platform: Target platform
            priority: Priority 1-5 (1=highest)

        Returns:
            Idea ID
        """
        idea_id = self._next_id
        self._next_id += 1

        self.event_store.emit(
            event_type=IDEA_CREATED,
            entity_type=self.ENTITY_TYPE,
            entity_id=idea_id,
            payload={
                "title": title,
                "description": description,
                "platform": platform.value,
                "priority": max(1, min(5, priority)),
                "status": IdeaStatus.DRAFT.value,
            }
        )
        return idea_id

    def update(
        self,
        idea_id: int,
        title: str = None,
        description: str = None,
        platform: Platform = None
    ) -> bool:
        """
        Update an idea's details.

        Args:
            idea_id: Idea ID
            title: New title (optional)
            description: New description (optional)
            platform: New platform (optional)

        Returns:
            True if idea exists and was updated
        """
        idea = self.get(idea_id)
        if not idea or idea.get("status") == IdeaStatus.ARCHIVED.value:
            return False

        payload = {}
        if title is not None:
            payload["title"] = title
        if description is not None:
            payload["description"] = description
        if platform is not None:
            payload["platform"] = platform.value

        if not payload:
            return False

        self.event_store.emit(
            event_type=IDEA_UPDATED,
            entity_type=self.ENTITY_TYPE,
            entity_id=idea_id,
            payload=payload
        )
        return True

    def set_status(self, idea_id: int, status: IdeaStatus) -> bool:
        """
        Change an idea's status.

        Args:
            idea_id: Idea ID
            status: New status

        Returns:
            True if idea exists and status was changed
        """
        idea = self.get(idea_id)
        if not idea:
            return False

        self.event_store.emit(
            event_type=IDEA_STATUS_CHANGED,
            entity_type=self.ENTITY_TYPE,
            entity_id=idea_id,
            payload={"status": status.value}
        )
        return True

    def prioritize(self, idea_id: int, priority: int) -> bool:
        """
        Set an idea's priority.

        Args:
            idea_id: Idea ID
            priority: Priority 1-5 (1=highest)

        Returns:
            True if idea exists and was prioritized
        """
        idea = self.get(idea_id)
        if not idea or idea.get("status") == IdeaStatus.ARCHIVED.value:
            return False

        self.event_store.emit(
            event_type=IDEA_PRIORITIZED,
            entity_type=self.ENTITY_TYPE,
            entity_id=idea_id,
            payload={"priority": max(1, min(5, priority))}
        )
        return True

    def get(self, idea_id: int) -> Optional[dict]:
        """
        Get idea state by projecting from events.

        Args:
            idea_id: Idea ID

        Returns:
            Idea state dict or None if not found
        """
        events = self.event_store.explain(self.ENTITY_TYPE, idea_id)
        if not events:
            return None

        return self._project_idea(idea_id, events)

    def _project_idea(self, idea_id: int, events: list[dict]) -> dict:
        """Project idea state from events."""
        state = {
            "id": idea_id,
            "title": "",
            "description": "",
            "platform": Platform.OTHER.value,
            "status": IdeaStatus.DRAFT.value,
            "priority": 3,
            "created_at": None,
            "updated_at": None,
        }

        for event in events:
            payload = event["payload"]
            timestamp = event["timestamp"]

            if event["event_type"] == IDEA_CREATED:
                state["title"] = payload.get("title", "")
                state["description"] = payload.get("description", "")
                state["platform"] = payload.get("platform", Platform.OTHER.value)
                state["status"] = payload.get("status", IdeaStatus.DRAFT.value)
                state["priority"] = payload.get("priority", 3)
                state["created_at"] = timestamp

            elif event["event_type"] == IDEA_UPDATED:
                if "title" in payload:
                    state["title"] = payload["title"]
                if "description" in payload:
                    state["description"] = payload["description"]
                if "platform" in payload:
                    state["platform"] = payload["platform"]
                state["updated_at"] = timestamp

            elif event["event_type"] == IDEA_STATUS_CHANGED:
                state["status"] = payload.get("status", state["status"])
                state["updated_at"] = timestamp

            elif event["event_type"] == IDEA_PRIORITIZED:
                state["priority"] = payload.get("priority", state["priority"])
                state["updated_at"] = timestamp

        return state

    def list_ideas(
        self,
        platform: Platform = None,
        status: IdeaStatus = None,
        include_archived: bool = False
    ) -> list[dict]:
        """
        List ideas with optional filters.

        Args:
            platform: Filter by platform
            status: Filter by status
            include_archived: Include archived ideas

        Returns:
            List of idea state dicts sorted by priority
        """
        created_events = self.event_store.query(
            entity_type=self.ENTITY_TYPE,
            event_type=IDEA_CREATED
        )

        ideas = []
        for event in created_events:
            idea_id = int(event["entity_id"])
            idea = self.get(idea_id)
            if idea:
                if not include_archived and idea["status"] == IdeaStatus.ARCHIVED.value:
                    continue
                if platform and idea["platform"] != platform.value:
                    continue
                if status and idea["status"] != status.value:
                    continue
                ideas.append(idea)

        # Sort by priority (1=highest), then by created_at
        ideas.sort(key=lambda i: (i["priority"], i.get("created_at", "")))
        return ideas

    def get_platforms(self) -> list[str]:
        """Get all platforms with ideas."""
        ideas = self.list_ideas(include_archived=False)
        platforms = set(idea["platform"] for idea in ideas)
        return sorted(platforms)

    def explain(self, idea_id: int) -> list[dict]:
        """
        Get event history for an idea (audit trail).

        Args:
            idea_id: Idea ID

        Returns:
            List of events in chronological order
        """
        return self.event_store.explain(self.ENTITY_TYPE, idea_id)
