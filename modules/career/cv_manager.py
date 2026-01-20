"""
CV/Resume Manager (CAR-002) - Event-sourced CV entry management.

Follows the Event Spine pattern: state derived from events only.
Events: ENTRY_ADDED, ENTRY_UPDATED, ENTRY_ARCHIVED
"""

from enum import Enum
from typing import Optional

from modules.core.database import Database, get_database
from modules.core.event_store import EventStore, get_event_store

# Event types
ENTRY_ADDED = "ENTRY_ADDED"
ENTRY_UPDATED = "ENTRY_UPDATED"
ENTRY_ARCHIVED = "ENTRY_ARCHIVED"


class EntryType(Enum):
    EXPERIENCE = "experience"
    EDUCATION = "education"
    SKILL = "skill"
    PROJECT = "project"
    CERTIFICATION = "certification"


class CVManager:
    """Event-sourced CV/resume entry manager."""

    ENTITY_TYPE = "cv_entry"

    def __init__(self, db: Optional[Database] = None, event_store: Optional[EventStore] = None):
        self.db = db or get_database()
        self.event_store = event_store or get_event_store()

    def add(
        self,
        entry_type: EntryType,
        title: str,
        organization: str = "",
        description: str = "",
        start_date: str = "",
        end_date: str = "",
        tags: str = "",
        highlights: str = ""
    ) -> int:
        """Add a new CV entry. Returns entry ID."""
        entry_id = self._get_next_id()
        payload = {
            "entry_type": entry_type.value,
            "title": title,
            "organization": organization,
            "description": description,
            "start_date": start_date,
            "end_date": end_date,
            "tags": tags,
            "highlights": highlights,
        }
        self.event_store.emit(ENTRY_ADDED, self.ENTITY_TYPE, entry_id, payload)
        return entry_id

    def update(self, entry_id: int, **kwargs) -> bool:
        """Update entry fields. Returns True if successful."""
        entry = self.get(entry_id)
        if not entry or entry["archived"]:
            return False
        valid_fields = {"title", "organization", "description", "start_date",
                        "end_date", "tags", "highlights"}
        payload = {k: v for k, v in kwargs.items() if k in valid_fields and v is not None}
        if not payload:
            return False
        self.event_store.emit(ENTRY_UPDATED, self.ENTITY_TYPE, entry_id, payload)
        return True

    def archive(self, entry_id: int) -> bool:
        """Archive an entry (soft delete)."""
        entry = self.get(entry_id)
        if not entry or entry["archived"]:
            return False
        self.event_store.emit(ENTRY_ARCHIVED, self.ENTITY_TYPE, entry_id, {"archived": True})
        return True

    def get(self, entry_id: int) -> Optional[dict]:
        """Get entry by projecting from events."""
        events = self.event_store.explain(self.ENTITY_TYPE, entry_id)
        if not events:
            return None
        return self._project(entry_id, events)

    def list_entries(
        self,
        entry_type: Optional[EntryType] = None,
        include_archived: bool = False,
        limit: int = 100
    ) -> list[dict]:
        """List entries with optional filters."""
        all_events = self.event_store.query(entity_type=self.ENTITY_TYPE, limit=10000)
        entry_ids = sorted(set(int(e["entity_id"]) for e in all_events))
        results = []
        for eid in entry_ids:
            entry = self.get(eid)
            if not entry:
                continue
            if not include_archived and entry["archived"]:
                continue
            if entry_type and entry["entry_type"] != entry_type.value:
                continue
            results.append(entry)
        return results[:limit]

    def export(self, include_archived: bool = False) -> str:
        """Export formatted CV summary."""
        entries = self.list_entries(include_archived=include_archived)

        sections = {
            "experience": ("WORK EXPERIENCE", []),
            "education": ("EDUCATION", []),
            "skill": ("SKILLS", []),
            "project": ("PROJECTS", []),
            "certification": ("CERTIFICATIONS", []),
        }

        for entry in entries:
            etype = entry["entry_type"]
            if etype in sections:
                sections[etype][1].append(entry)

        output = ["=" * 50, "CURRICULUM VITAE", "=" * 50, ""]

        for etype, (header, items) in sections.items():
            if items:
                output.append(f"\n{header}")
                output.append("-" * len(header))
                for item in items:
                    org = f" @ {item['organization']}" if item["organization"] else ""
                    dates = ""
                    if item["start_date"]:
                        dates = f" ({item['start_date']} - {item['end_date'] or 'present'})"
                    output.append(f"  • {item['title']}{org}{dates}")
                    if item["description"]:
                        output.append(f"    {item['description']}")

        return "\n".join(output)

    def explain(self, entry_id: int) -> list[dict]:
        """Get full event history for an entry."""
        return self.event_store.explain(self.ENTITY_TYPE, entry_id)

    def _get_next_id(self) -> int:
        """Get next available entry ID."""
        events = self.event_store.query(entity_type=self.ENTITY_TYPE, event_type=ENTRY_ADDED, limit=10000)
        if not events:
            return 1
        return max(int(e["entity_id"]) for e in events) + 1

    def _project(self, entry_id: int, events: list[dict]) -> dict:
        """Project entry state from events."""
        state = {
            "id": entry_id, "entry_type": "", "title": "", "organization": "",
            "description": "", "start_date": "", "end_date": "", "tags": "",
            "highlights": "", "archived": False, "created_at": None,
        }
        for event in events:
            etype = event["event_type"]
            payload = event["payload"]
            if etype == ENTRY_ADDED:
                state.update(payload)
                state["created_at"] = event["timestamp"]
            elif etype == ENTRY_UPDATED:
                state.update(payload)
            elif etype == ENTRY_ARCHIVED:
                state["archived"] = True
        return state
