"""
Atlas Personal OS - Note Manager (KNOW-002)

Event-sourced note taking implementing the Event Spine invariant:
COMMAND → EVENT → PROJECTION

Notes are projections computed entirely from events.
Supports full-text search, tags, and audit trail.
"""

from datetime import datetime
from typing import Optional, Any
from modules.core.database import Database, get_database
from modules.core.event_store import EventStore, get_event_store


# Event Types
NOTE_CREATED = "NOTE_CREATED"
NOTE_UPDATED = "NOTE_UPDATED"
NOTE_ARCHIVED = "NOTE_ARCHIVED"
NOTE_TAGGED = "NOTE_TAGGED"


class NoteManager:
    """
    Event-sourced note manager.

    All state is derived from events - no direct database mutations.
    """

    ENTITY_TYPE = "note"

    def __init__(
        self,
        db: Optional[Database] = None,
        event_store: Optional[EventStore] = None
    ):
        """Initialize note manager with event store."""
        self.db = db or get_database()
        self.event_store = event_store or get_event_store()
        self._next_id = self._compute_next_id()

    def _compute_next_id(self) -> int:
        """Compute next note ID from existing events."""
        events = self.event_store.query(
            entity_type=self.ENTITY_TYPE,
            event_type=NOTE_CREATED
        )
        if not events:
            return 1
        max_id = max(int(e["entity_id"]) for e in events)
        return max_id + 1

    def create(self, title: str, content: str = "", tags: list[str] = None) -> int:
        """
        Create a new note.

        Args:
            title: Note title
            content: Note content (markdown supported)
            tags: Optional list of tags

        Returns:
            Note ID
        """
        note_id = self._next_id
        self._next_id += 1

        self.event_store.emit(
            event_type=NOTE_CREATED,
            entity_type=self.ENTITY_TYPE,
            entity_id=note_id,
            payload={
                "title": title,
                "content": content,
                "tags": tags or [],
            }
        )
        return note_id

    def update(self, note_id: int, title: str = None, content: str = None) -> bool:
        """
        Update a note's title or content.

        Args:
            note_id: Note ID
            title: New title (optional)
            content: New content (optional)

        Returns:
            True if note exists and was updated
        """
        note = self.get(note_id)
        if not note or note.get("archived"):
            return False

        payload = {}
        if title is not None:
            payload["title"] = title
        if content is not None:
            payload["content"] = content

        if not payload:
            return False

        self.event_store.emit(
            event_type=NOTE_UPDATED,
            entity_type=self.ENTITY_TYPE,
            entity_id=note_id,
            payload=payload
        )
        return True

    def archive(self, note_id: int) -> bool:
        """
        Archive a note (soft delete).

        Args:
            note_id: Note ID

        Returns:
            True if note exists and was archived
        """
        note = self.get(note_id)
        if not note or note.get("archived"):
            return False

        self.event_store.emit(
            event_type=NOTE_ARCHIVED,
            entity_type=self.ENTITY_TYPE,
            entity_id=note_id,
            payload={"archived": True}
        )
        return True

    def tag(self, note_id: int, tags: list[str]) -> bool:
        """
        Add or update tags on a note.

        Args:
            note_id: Note ID
            tags: List of tags to set

        Returns:
            True if note exists and was tagged
        """
        note = self.get(note_id)
        if not note or note.get("archived"):
            return False

        self.event_store.emit(
            event_type=NOTE_TAGGED,
            entity_type=self.ENTITY_TYPE,
            entity_id=note_id,
            payload={"tags": tags}
        )
        return True

    def get(self, note_id: int) -> Optional[dict]:
        """
        Get note state by projecting from events.

        Args:
            note_id: Note ID

        Returns:
            Note state dict or None if not found
        """
        events = self.event_store.explain(self.ENTITY_TYPE, note_id)
        if not events:
            return None

        return self._project_note(note_id, events)

    def _project_note(self, note_id: int, events: list[dict]) -> dict:
        """Project note state from events."""
        state = {
            "id": note_id,
            "title": "",
            "content": "",
            "tags": [],
            "archived": False,
            "created_at": None,
            "updated_at": None,
        }

        for event in events:
            payload = event["payload"]
            timestamp = event["timestamp"]

            if event["event_type"] == NOTE_CREATED:
                state["title"] = payload.get("title", "")
                state["content"] = payload.get("content", "")
                state["tags"] = payload.get("tags", [])
                state["created_at"] = timestamp

            elif event["event_type"] == NOTE_UPDATED:
                if "title" in payload:
                    state["title"] = payload["title"]
                if "content" in payload:
                    state["content"] = payload["content"]
                state["updated_at"] = timestamp

            elif event["event_type"] == NOTE_ARCHIVED:
                state["archived"] = payload.get("archived", True)
                state["updated_at"] = timestamp

            elif event["event_type"] == NOTE_TAGGED:
                state["tags"] = payload.get("tags", [])
                state["updated_at"] = timestamp

        return state

    def list_notes(self, include_archived: bool = False, tag: str = None) -> list[dict]:
        """
        List all notes by projecting from events.

        Args:
            include_archived: Include archived notes
            tag: Filter by tag

        Returns:
            List of note state dicts
        """
        created_events = self.event_store.query(
            entity_type=self.ENTITY_TYPE,
            event_type=NOTE_CREATED
        )

        notes = []
        for event in created_events:
            note_id = int(event["entity_id"])
            note = self.get(note_id)
            if note:
                if not include_archived and note.get("archived"):
                    continue
                if tag and tag not in note.get("tags", []):
                    continue
                notes.append(note)

        # Sort by created_at descending (most recent first)
        notes.sort(key=lambda n: n.get("created_at", ""), reverse=True)
        return notes

    def search(self, query: str, include_archived: bool = False) -> list[dict]:
        """
        Search notes by title and content.

        Args:
            query: Search query (case-insensitive)
            include_archived: Include archived notes

        Returns:
            List of matching notes
        """
        query_lower = query.lower()
        notes = self.list_notes(include_archived=include_archived)

        results = []
        for note in notes:
            title = note.get("title", "").lower()
            content = note.get("content", "").lower()
            if query_lower in title or query_lower in content:
                results.append(note)

        return results

    def get_tags(self) -> list[str]:
        """
        Get all unique tags across notes.

        Returns:
            Sorted list of unique tags
        """
        notes = self.list_notes(include_archived=False)
        all_tags = set()
        for note in notes:
            all_tags.update(note.get("tags", []))
        return sorted(all_tags)

    def explain(self, note_id: int) -> list[dict]:
        """
        Get event history for a note (audit trail).

        Args:
            note_id: Note ID

        Returns:
            List of events in chronological order
        """
        return self.event_store.explain(self.ENTITY_TYPE, note_id)
