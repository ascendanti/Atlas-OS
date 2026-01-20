"""
Atlas Personal OS - Publication Tracker (CAR-001)

Event-sourced publication tracking following the Event Spine invariant.
State is derived entirely from events - no direct table mutations.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from enum import Enum

from modules.core.database import Database, get_database
from modules.core.event_store import EventStore, get_event_store


# Event types
PUB_CREATED = "PUB_CREATED"
PUB_UPDATED = "PUB_UPDATED"
PUB_SUBMITTED = "PUB_SUBMITTED"
PUB_ACCEPTED = "PUB_ACCEPTED"
PUB_REJECTED = "PUB_REJECTED"
PUB_PUBLISHED = "PUB_PUBLISHED"


class VenueType(Enum):
    """Publication venue types."""
    JOURNAL = "journal"
    CONFERENCE = "conference"
    PREPRINT = "preprint"
    BOOK = "book"
    OTHER = "other"


class PubStatus(Enum):
    """Publication status."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    PUBLISHED = "published"


class PublicationTracker:
    """Publication tracking system using event sourcing."""

    ENTITY_TYPE = "publication"

    def __init__(self, db: Optional[Database] = None, event_store: Optional[EventStore] = None):
        """Initialize publication tracker."""
        self.db = db or get_database()
        self.event_store = event_store or get_event_store()

    def add(
        self,
        title: str,
        authors: str = "",
        venue: VenueType = VenueType.OTHER,
        abstract: str = "",
        tags: str = ""
    ) -> int:
        """
        Add a new publication.

        Args:
            title: Publication title
            authors: Comma-separated author names
            venue: Venue type (journal/conference/preprint/book/other)
            abstract: Publication abstract
            tags: Comma-separated tags

        Returns:
            Publication ID
        """
        pub_id = self._get_next_id()

        self.event_store.emit(
            event_type=PUB_CREATED,
            entity_type=self.ENTITY_TYPE,
            entity_id=pub_id,
            payload={
                "title": title,
                "authors": authors,
                "venue": venue.value,
                "abstract": abstract,
                "tags": tags,
                "status": PubStatus.DRAFT.value,
            }
        )
        return pub_id

    def _get_next_id(self) -> int:
        """Get the next available publication ID."""
        events = self.event_store.query(
            entity_type=self.ENTITY_TYPE,
            event_type=PUB_CREATED
        )
        if not events:
            return 1
        max_id = max(int(e["entity_id"]) for e in events)
        return max_id + 1

    def get(self, pub_id: int) -> Optional[dict]:
        """Get publication state by projecting from events."""
        events = self.event_store.query(
            entity_type=self.ENTITY_TYPE,
            entity_id=pub_id
        )
        if not events:
            return None
        return self._project(events)

    def _project(self, events: list[dict]) -> dict:
        """Project publication state from events."""
        state = {
            "id": None,
            "title": "",
            "authors": "",
            "venue": VenueType.OTHER.value,
            "abstract": "",
            "tags": "",
            "status": PubStatus.DRAFT.value,
            "submission_date": None,
            "acceptance_date": None,
            "rejection_date": None,
            "publication_date": None,
            "doi": None,
            "url": None,
        }

        for event in events:
            payload = event["payload"]
            if isinstance(payload, str):
                import json
                payload = json.loads(payload)

            state["id"] = int(event["entity_id"])

            if event["event_type"] == PUB_CREATED:
                state.update({
                    "title": payload.get("title", ""),
                    "authors": payload.get("authors", ""),
                    "venue": payload.get("venue", VenueType.OTHER.value),
                    "abstract": payload.get("abstract", ""),
                    "tags": payload.get("tags", ""),
                    "status": payload.get("status", PubStatus.DRAFT.value),
                })
            elif event["event_type"] == PUB_UPDATED:
                for key in ["title", "authors", "venue", "abstract", "tags", "doi", "url"]:
                    if key in payload:
                        state[key] = payload[key]
            elif event["event_type"] == PUB_SUBMITTED:
                state["status"] = PubStatus.SUBMITTED.value
                state["submission_date"] = payload.get("submitted_at")
            elif event["event_type"] == PUB_ACCEPTED:
                state["status"] = PubStatus.ACCEPTED.value
                state["acceptance_date"] = payload.get("accepted_at")
            elif event["event_type"] == PUB_REJECTED:
                state["status"] = PubStatus.REJECTED.value
                state["rejection_date"] = payload.get("rejected_at")
            elif event["event_type"] == PUB_PUBLISHED:
                state["status"] = PubStatus.PUBLISHED.value
                state["publication_date"] = payload.get("published_at")
                if "doi" in payload:
                    state["doi"] = payload["doi"]
                if "url" in payload:
                    state["url"] = payload["url"]

        return state

    def update(self, pub_id: int, **kwargs) -> bool:
        """Update publication details."""
        pub = self.get(pub_id)
        if not pub:
            return False

        allowed = ["title", "authors", "venue", "abstract", "tags", "doi", "url"]
        updates = {}
        for k, v in kwargs.items():
            if k in allowed and v is not None:
                if k == "venue" and isinstance(v, VenueType):
                    updates[k] = v.value
                else:
                    updates[k] = v

        if not updates:
            return False

        self.event_store.emit(
            event_type=PUB_UPDATED,
            entity_type=self.ENTITY_TYPE,
            entity_id=pub_id,
            payload=updates
        )
        return True

    def submit(self, pub_id: int) -> bool:
        """Mark publication as submitted."""
        pub = self.get(pub_id)
        if not pub or pub["status"] != PubStatus.DRAFT.value:
            return False

        self.event_store.emit(
            event_type=PUB_SUBMITTED,
            entity_type=self.ENTITY_TYPE,
            entity_id=pub_id,
            payload={"submitted_at": datetime.now().isoformat()}
        )
        return True

    def accept(self, pub_id: int) -> bool:
        """Mark publication as accepted."""
        pub = self.get(pub_id)
        if not pub or pub["status"] != PubStatus.SUBMITTED.value:
            return False

        self.event_store.emit(
            event_type=PUB_ACCEPTED,
            entity_type=self.ENTITY_TYPE,
            entity_id=pub_id,
            payload={"accepted_at": datetime.now().isoformat()}
        )
        return True

    def reject(self, pub_id: int) -> bool:
        """Mark publication as rejected."""
        pub = self.get(pub_id)
        if not pub or pub["status"] != PubStatus.SUBMITTED.value:
            return False

        self.event_store.emit(
            event_type=PUB_REJECTED,
            entity_type=self.ENTITY_TYPE,
            entity_id=pub_id,
            payload={"rejected_at": datetime.now().isoformat()}
        )
        return True

    def publish(self, pub_id: int, doi: str = "", url: str = "") -> bool:
        """Mark publication as published."""
        pub = self.get(pub_id)
        if not pub or pub["status"] != PubStatus.ACCEPTED.value:
            return False

        self.event_store.emit(
            event_type=PUB_PUBLISHED,
            entity_type=self.ENTITY_TYPE,
            entity_id=pub_id,
            payload={
                "published_at": datetime.now().isoformat(),
                "doi": doi,
                "url": url,
            }
        )
        return True

    def list_publications(
        self,
        status: Optional[PubStatus] = None,
        venue: Optional[VenueType] = None,
        limit: int = 100
    ) -> list[dict]:
        """List all publications, optionally filtered."""
        events = self.event_store.query(
            entity_type=self.ENTITY_TYPE,
            event_type=PUB_CREATED
        )

        pub_ids = sorted(set(int(e["entity_id"]) for e in events))
        publications = []

        for pid in pub_ids:
            pub = self.get(pid)
            if pub:
                if status and pub["status"] != status.value:
                    continue
                if venue and pub["venue"] != venue.value:
                    continue
                publications.append(pub)

        return publications[:limit]

    def explain(self, pub_id: int) -> list[dict]:
        """Get event history for a publication (audit trail)."""
        return self.event_store.query(
            entity_type=self.ENTITY_TYPE,
            entity_id=pub_id
        )
