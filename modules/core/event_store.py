"""
Atlas Personal OS - Event Store (CORE-004)

Canonical event storage implementing the Event Spine invariant:
COMMAND → EVENT → PROJECTION → (optional) POLICY

All state changes emit events here; projections derive state from events.
"""

import json
from datetime import datetime
from typing import Optional, Any
from modules.core.database import Database, get_database


class EventStore:
    """
    Canonical event store for Atlas Personal OS.

    Events are immutable facts that describe what happened.
    Projections read events to derive current state.
    """

    TABLE_NAME = "events"
    SCHEMA = """
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_type TEXT NOT NULL,
        entity_type TEXT NOT NULL,
        entity_id TEXT NOT NULL,
        payload TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    """

    def __init__(self, db: Optional[Database] = None):
        """Initialize event store with database."""
        self.db = db or get_database()
        self._ensure_table()

    def _ensure_table(self) -> None:
        """Create events table if it doesn't exist."""
        self.db.create_table(self.TABLE_NAME, self.SCHEMA)
        # Create index for common queries
        self.db.execute(
            f"CREATE INDEX IF NOT EXISTS idx_events_entity "
            f"ON {self.TABLE_NAME} (entity_type, entity_id)"
        )
        self.db.execute(
            f"CREATE INDEX IF NOT EXISTS idx_events_type "
            f"ON {self.TABLE_NAME} (event_type)"
        )
        self.db.connection.commit()

    def emit(
        self,
        event_type: str,
        entity_type: str,
        entity_id: str | int,
        payload: dict[str, Any]
    ) -> int:
        """
        Emit an event to the store.

        Args:
            event_type: Type of event (e.g., "TASK_CREATED", "GOAL_DEFINED")
            entity_type: Type of entity (e.g., "task", "goal")
            entity_id: ID of the entity
            payload: Event data as dictionary

        Returns:
            ID of the created event
        """
        data = {
            "event_type": event_type,
            "entity_type": entity_type,
            "entity_id": str(entity_id),
            "payload": json.dumps(payload),
            "timestamp": datetime.now().isoformat(),
        }
        return self.db.insert(self.TABLE_NAME, data)

    def query(
        self,
        entity_type: Optional[str] = None,
        entity_id: Optional[str | int] = None,
        event_type: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: int = 1000
    ) -> list[dict]:
        """
        Query events with optional filters.

        Args:
            entity_type: Filter by entity type
            entity_id: Filter by entity ID
            event_type: Filter by event type
            since: Filter events after this timestamp
            limit: Maximum events to return

        Returns:
            List of event dictionaries with parsed payloads
        """
        conditions = []
        params = []

        if entity_type:
            conditions.append("entity_type = ?")
            params.append(entity_type)

        if entity_id is not None:
            conditions.append("entity_id = ?")
            params.append(str(entity_id))

        if event_type:
            conditions.append("event_type = ?")
            params.append(event_type)

        if since:
            conditions.append("timestamp >= ?")
            params.append(since.isoformat())

        where_clause = " AND ".join(conditions) if conditions else "1=1"
        sql = f"""
            SELECT * FROM {self.TABLE_NAME}
            WHERE {where_clause}
            ORDER BY timestamp ASC, id ASC
            LIMIT ?
        """
        params.append(limit)

        rows = self.db.fetchall(sql, tuple(params))
        return [self._row_to_dict(row) for row in rows]

    def explain(self, entity_type: str, entity_id: str | int) -> list[dict]:
        """
        Get chronological event history for an entity.

        Answers: "Why is this entity in its current state?"

        Args:
            entity_type: Type of entity
            entity_id: ID of the entity

        Returns:
            Chronological list of events for the entity
        """
        return self.query(entity_type=entity_type, entity_id=entity_id)

    def _row_to_dict(self, row) -> dict:
        """Convert database row to dictionary with parsed payload."""
        result = dict(row)
        if "payload" in result and result["payload"]:
            result["payload"] = json.loads(result["payload"])
        return result

    def count(
        self,
        entity_type: Optional[str] = None,
        event_type: Optional[str] = None
    ) -> int:
        """
        Count events with optional filters.

        Args:
            entity_type: Filter by entity type
            event_type: Filter by event type

        Returns:
            Number of matching events
        """
        conditions = []
        params = []

        if entity_type:
            conditions.append("entity_type = ?")
            params.append(entity_type)

        if event_type:
            conditions.append("event_type = ?")
            params.append(event_type)

        where_clause = " AND ".join(conditions) if conditions else "1=1"
        sql = f"SELECT COUNT(*) as count FROM {self.TABLE_NAME} WHERE {where_clause}"

        row = self.db.fetchone(sql, tuple(params))
        return row["count"] if row else 0


# Singleton instance
_default_store: Optional[EventStore] = None


def get_event_store() -> EventStore:
    """Get the default event store instance."""
    global _default_store
    if _default_store is None:
        _default_store = EventStore()
    return _default_store


def emit_event(
    event_type: str,
    entity_type: str,
    entity_id: str | int,
    payload: dict[str, Any]
) -> int:
    """Convenience function to emit an event using default store."""
    return get_event_store().emit(event_type, entity_type, entity_id, payload)


def query_events(
    entity_type: Optional[str] = None,
    entity_id: Optional[str | int] = None,
    event_type: Optional[str] = None,
    since: Optional[datetime] = None,
    limit: int = 1000
) -> list[dict]:
    """Convenience function to query events using default store."""
    return get_event_store().query(entity_type, entity_id, event_type, since, limit)


def explain(entity_type: str, entity_id: str | int) -> list[dict]:
    """Convenience function to explain an entity's history."""
    return get_event_store().explain(entity_type, entity_id)
