"""
Event Reminder System (LIFE-004) - Event-sourced reminders and calendar events.

Follows the Event Spine pattern: state derived from events only.
Events: REMINDER_CREATED, REMINDER_UPDATED, REMINDER_TRIGGERED,
        REMINDER_SNOOZED, REMINDER_COMPLETED, REMINDER_ARCHIVED
"""

from datetime import datetime, date, timedelta
from enum import Enum
from typing import Optional

from modules.core.database import Database, get_database
from modules.core.event_store import EventStore, get_event_store

# Event types
REMINDER_CREATED = "REMINDER_CREATED"
REMINDER_UPDATED = "REMINDER_UPDATED"
REMINDER_TRIGGERED = "REMINDER_TRIGGERED"
REMINDER_SNOOZED = "REMINDER_SNOOZED"
REMINDER_COMPLETED = "REMINDER_COMPLETED"
REMINDER_ARCHIVED = "REMINDER_ARCHIVED"


class Recurrence(Enum):
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class EventReminder:
    """Event-sourced reminder/calendar event manager."""

    ENTITY_TYPE = "reminder"

    def __init__(self, db: Optional[Database] = None, event_store: Optional[EventStore] = None):
        self.db = db or get_database()
        self.event_store = event_store or get_event_store()

    def add(
        self,
        title: str,
        event_date: str,
        event_time: str = "",
        description: str = "",
        reminder_minutes: int = 30,
        recurrence: Recurrence = Recurrence.NONE,
        contact_id: Optional[int] = None,
        tags: str = ""
    ) -> int:
        """Create a new reminder. Returns reminder ID."""
        reminder_id = self._get_next_id()
        payload = {
            "title": title,
            "event_date": event_date,
            "event_time": event_time,
            "description": description,
            "reminder_minutes": reminder_minutes,
            "recurrence": recurrence.value,
            "contact_id": contact_id,
            "tags": tags,
        }
        self.event_store.emit(REMINDER_CREATED, self.ENTITY_TYPE, reminder_id, payload)
        return reminder_id

    def update(self, reminder_id: int, **kwargs) -> bool:
        """Update reminder fields. Returns True if successful."""
        reminder = self.get(reminder_id)
        if not reminder or reminder["archived"] or reminder["completed"]:
            return False
        valid_fields = {"title", "event_date", "event_time", "description",
                        "reminder_minutes", "recurrence", "contact_id", "tags"}
        payload = {k: v for k, v in kwargs.items() if k in valid_fields and v is not None}
        if not payload:
            return False
        if "recurrence" in payload and isinstance(payload["recurrence"], Recurrence):
            payload["recurrence"] = payload["recurrence"].value
        self.event_store.emit(REMINDER_UPDATED, self.ENTITY_TYPE, reminder_id, payload)
        return True

    def trigger(self, reminder_id: int) -> bool:
        """Mark reminder as triggered (notification sent)."""
        reminder = self.get(reminder_id)
        if not reminder or reminder["archived"] or reminder["completed"]:
            return False
        self.event_store.emit(REMINDER_TRIGGERED, self.ENTITY_TYPE, reminder_id,
                              {"triggered_at": datetime.now().isoformat()})
        return True

    def snooze(self, reminder_id: int, minutes: int = 15) -> bool:
        """Snooze a reminder by specified minutes."""
        reminder = self.get(reminder_id)
        if not reminder or reminder["archived"] or reminder["completed"]:
            return False
        self.event_store.emit(REMINDER_SNOOZED, self.ENTITY_TYPE, reminder_id,
                              {"snooze_minutes": minutes, "snoozed_at": datetime.now().isoformat()})
        return True

    def complete(self, reminder_id: int) -> bool:
        """Mark reminder as completed."""
        reminder = self.get(reminder_id)
        if not reminder or reminder["archived"] or reminder["completed"]:
            return False
        self.event_store.emit(REMINDER_COMPLETED, self.ENTITY_TYPE, reminder_id,
                              {"completed_at": datetime.now().isoformat()})
        return True

    def archive(self, reminder_id: int) -> bool:
        """Archive a reminder (soft delete)."""
        reminder = self.get(reminder_id)
        if not reminder or reminder["archived"]:
            return False
        self.event_store.emit(REMINDER_ARCHIVED, self.ENTITY_TYPE, reminder_id,
                              {"archived_at": datetime.now().isoformat()})
        return True

    def get(self, reminder_id: int) -> Optional[dict]:
        """Get reminder by projecting from events."""
        events = self.event_store.explain(self.ENTITY_TYPE, reminder_id)
        if not events:
            return None
        return self._project(reminder_id, events)

    def list_reminders(
        self,
        include_completed: bool = False,
        include_archived: bool = False,
        tag: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        limit: int = 100
    ) -> list[dict]:
        """List reminders with optional filters."""
        all_events = self.event_store.query(entity_type=self.ENTITY_TYPE, limit=10000)
        reminder_ids = sorted(set(int(e["entity_id"]) for e in all_events))
        results = []
        for rid in reminder_ids:
            reminder = self.get(rid)
            if not reminder:
                continue
            if not include_archived and reminder["archived"]:
                continue
            if not include_completed and reminder["completed"]:
                continue
            if tag and tag.lower() not in (reminder["tags"] or "").lower():
                continue
            if from_date and reminder["event_date"] < from_date:
                continue
            if to_date and reminder["event_date"] > to_date:
                continue
            results.append(reminder)
        results.sort(key=lambda r: (r["event_date"], r["event_time"] or ""))
        return results[:limit]

    def upcoming(self, days: int = 7) -> list[dict]:
        """Get reminders for the next N days."""
        today = date.today().isoformat()
        future = (date.today() + timedelta(days=days)).isoformat()
        return self.list_reminders(from_date=today, to_date=future)

    def explain(self, reminder_id: int) -> list[dict]:
        """Get full event history for a reminder."""
        return self.event_store.explain(self.ENTITY_TYPE, reminder_id)

    def _get_next_id(self) -> int:
        """Get next available reminder ID."""
        events = self.event_store.query(entity_type=self.ENTITY_TYPE, event_type=REMINDER_CREATED, limit=10000)
        if not events:
            return 1
        return max(int(e["entity_id"]) for e in events) + 1

    def _project(self, reminder_id: int, events: list[dict]) -> dict:
        """Project reminder state from events."""
        state = {
            "id": reminder_id, "title": "", "event_date": "", "event_time": "",
            "description": "", "reminder_minutes": 30, "recurrence": "none",
            "contact_id": None, "tags": "", "completed": False, "archived": False,
            "triggered_at": None, "snoozed_at": None, "snooze_minutes": 0,
            "completed_at": None, "created_at": None,
        }
        for event in events:
            etype = event["event_type"]
            payload = event["payload"]
            if etype == REMINDER_CREATED:
                state.update(payload)
                state["created_at"] = event["timestamp"]
            elif etype == REMINDER_UPDATED:
                state.update(payload)
            elif etype == REMINDER_TRIGGERED:
                state["triggered_at"] = payload.get("triggered_at")
            elif etype == REMINDER_SNOOZED:
                state["snoozed_at"] = payload.get("snoozed_at")
                state["snooze_minutes"] = payload.get("snooze_minutes", 15)
            elif etype == REMINDER_COMPLETED:
                state["completed"] = True
                state["completed_at"] = payload.get("completed_at")
            elif etype == REMINDER_ARCHIVED:
                state["archived"] = True
        return state
