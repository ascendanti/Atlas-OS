"""
Atlas Personal OS - PDF Library Indexer (KNOW-001)

Event-sourced PDF indexing following the Event Spine invariant.
State is derived entirely from events - no direct table mutations.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional
from enum import Enum

from modules.core.database import Database, get_database
from modules.core.event_store import EventStore, get_event_store


# Event types
PDF_INDEXED = "PDF_INDEXED"
PDF_UPDATED = "PDF_UPDATED"
PDF_TAGGED = "PDF_TAGGED"
PDF_NOTE_ADDED = "PDF_NOTE_ADDED"
PDF_ARCHIVED = "PDF_ARCHIVED"


class PDFCategory(Enum):
    """PDF category types."""
    RESEARCH = "research"
    BOOK = "book"
    ARTICLE = "article"
    MANUAL = "manual"
    OTHER = "other"


class PDFIndexer:
    """PDF library indexer using event sourcing."""

    ENTITY_TYPE = "pdf"

    def __init__(self, db: Optional[Database] = None, event_store: Optional[EventStore] = None):
        """Initialize PDF indexer."""
        self.db = db or get_database()
        self.event_store = event_store or get_event_store()

    def index(
        self,
        file_path: str,
        title: str = "",
        authors: str = "",
        category: PDFCategory = PDFCategory.OTHER,
        tags: str = "",
        page_count: int = 0
    ) -> int:
        """
        Index a new PDF file.

        Args:
            file_path: Path to the PDF file
            title: PDF title (extracted or manual)
            authors: Comma-separated author names
            category: PDF category
            tags: Comma-separated tags
            page_count: Number of pages

        Returns:
            PDF ID
        """
        pdf_id = self._get_next_id()

        # Use filename as title if not provided
        if not title:
            title = Path(file_path).stem

        self.event_store.emit(
            event_type=PDF_INDEXED,
            entity_type=self.ENTITY_TYPE,
            entity_id=pdf_id,
            payload={
                "file_path": file_path,
                "title": title,
                "authors": authors,
                "category": category.value,
                "tags": tags,
                "page_count": page_count,
                "indexed_at": datetime.now().isoformat(),
                "archived": False,
            }
        )
        return pdf_id

    def _get_next_id(self) -> int:
        """Get the next available PDF ID."""
        events = self.event_store.query(
            entity_type=self.ENTITY_TYPE,
            event_type=PDF_INDEXED
        )
        if not events:
            return 1
        max_id = max(int(e["entity_id"]) for e in events)
        return max_id + 1

    def get(self, pdf_id: int) -> Optional[dict]:
        """Get PDF state by projecting from events."""
        events = self.event_store.query(
            entity_type=self.ENTITY_TYPE,
            entity_id=pdf_id
        )
        if not events:
            return None
        return self._project(events)

    def _project(self, events: list[dict]) -> dict:
        """Project PDF state from events."""
        state = {
            "id": None,
            "file_path": "",
            "title": "",
            "authors": "",
            "category": PDFCategory.OTHER.value,
            "tags": "",
            "page_count": 0,
            "indexed_at": None,
            "notes": "",
            "archived": False,
        }

        for event in events:
            payload = event["payload"]
            if isinstance(payload, str):
                import json
                payload = json.loads(payload)

            state["id"] = int(event["entity_id"])

            if event["event_type"] == PDF_INDEXED:
                state.update({
                    "file_path": payload.get("file_path", ""),
                    "title": payload.get("title", ""),
                    "authors": payload.get("authors", ""),
                    "category": payload.get("category", PDFCategory.OTHER.value),
                    "tags": payload.get("tags", ""),
                    "page_count": payload.get("page_count", 0),
                    "indexed_at": payload.get("indexed_at"),
                    "archived": payload.get("archived", False),
                })
            elif event["event_type"] == PDF_UPDATED:
                for key in ["title", "authors", "category", "page_count"]:
                    if key in payload:
                        state[key] = payload[key]
            elif event["event_type"] == PDF_TAGGED:
                state["tags"] = payload.get("tags", "")
            elif event["event_type"] == PDF_NOTE_ADDED:
                existing = state.get("notes", "")
                new_note = payload.get("note", "")
                state["notes"] = f"{existing}\n{new_note}".strip() if existing else new_note
            elif event["event_type"] == PDF_ARCHIVED:
                state["archived"] = True

        return state

    def update(self, pdf_id: int, **kwargs) -> bool:
        """Update PDF details."""
        pdf = self.get(pdf_id)
        if not pdf or pdf["archived"]:
            return False

        allowed = ["title", "authors", "category", "page_count"]
        updates = {}
        for k, v in kwargs.items():
            if k in allowed and v is not None:
                if k == "category" and isinstance(v, PDFCategory):
                    updates[k] = v.value
                else:
                    updates[k] = v

        if not updates:
            return False

        self.event_store.emit(
            event_type=PDF_UPDATED,
            entity_type=self.ENTITY_TYPE,
            entity_id=pdf_id,
            payload=updates
        )
        return True

    def tag(self, pdf_id: int, tags: str) -> bool:
        """Set tags for a PDF."""
        pdf = self.get(pdf_id)
        if not pdf or pdf["archived"]:
            return False

        self.event_store.emit(
            event_type=PDF_TAGGED,
            entity_type=self.ENTITY_TYPE,
            entity_id=pdf_id,
            payload={"tags": tags}
        )
        return True

    def add_note(self, pdf_id: int, note: str) -> bool:
        """Add a note to a PDF."""
        pdf = self.get(pdf_id)
        if not pdf or pdf["archived"]:
            return False

        self.event_store.emit(
            event_type=PDF_NOTE_ADDED,
            entity_type=self.ENTITY_TYPE,
            entity_id=pdf_id,
            payload={"note": note, "added_at": datetime.now().isoformat()}
        )
        return True

    def archive(self, pdf_id: int) -> bool:
        """Archive a PDF (soft delete)."""
        pdf = self.get(pdf_id)
        if not pdf or pdf["archived"]:
            return False

        self.event_store.emit(
            event_type=PDF_ARCHIVED,
            entity_type=self.ENTITY_TYPE,
            entity_id=pdf_id,
            payload={"archived_at": datetime.now().isoformat()}
        )
        return True

    def list_pdfs(
        self,
        category: Optional[PDFCategory] = None,
        tag: Optional[str] = None,
        include_archived: bool = False,
        limit: int = 100
    ) -> list[dict]:
        """List all PDFs, optionally filtered."""
        events = self.event_store.query(
            entity_type=self.ENTITY_TYPE,
            event_type=PDF_INDEXED
        )

        pdf_ids = sorted(set(int(e["entity_id"]) for e in events))
        pdfs = []

        for pid in pdf_ids:
            pdf = self.get(pid)
            if pdf:
                if not include_archived and pdf["archived"]:
                    continue
                if category and pdf["category"] != category.value:
                    continue
                if tag and tag.lower() not in pdf["tags"].lower():
                    continue
                pdfs.append(pdf)

        return pdfs[:limit]

    def search(self, query: str, include_archived: bool = False) -> list[dict]:
        """Search PDFs by title, authors, or notes."""
        all_pdfs = self.list_pdfs(include_archived=include_archived, limit=1000)
        query_lower = query.lower()

        results = []
        for pdf in all_pdfs:
            if (query_lower in pdf["title"].lower() or
                query_lower in pdf["authors"].lower() or
                query_lower in pdf["notes"].lower()):
                results.append(pdf)

        return results

    def explain(self, pdf_id: int) -> list[dict]:
        """Get event history for a PDF (audit trail)."""
        return self.event_store.query(
            entity_type=self.ENTITY_TYPE,
            entity_id=pdf_id
        )
