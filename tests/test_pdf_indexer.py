"""
Tests for the PDF Library Indexer (KNOW-001).

Tests the PDF-as-projection pattern: state derived from events only.
"""

import pytest

from modules.core.database import Database
from modules.core.event_store import EventStore
from modules.knowledge.pdf_indexer import (
    PDFIndexer,
    PDFCategory,
    PDF_INDEXED,
    PDF_UPDATED,
    PDF_TAGGED,
    PDF_NOTE_ADDED,
    PDF_ARCHIVED,
)


@pytest.fixture
def pdf_indexer(temp_db):
    """Create a PDF indexer with a temporary database."""
    event_store = EventStore(db=temp_db)
    return PDFIndexer(db=temp_db, event_store=event_store)


class TestPDFIndex:
    """Tests for PDF indexing."""

    def test_index_returns_pdf_id(self, pdf_indexer):
        """index() should return the PDF ID."""
        pdf_id = pdf_indexer.index("/path/to/document.pdf")
        assert pdf_id == 1

    def test_index_multiple_pdfs(self, pdf_indexer):
        """index() should return incrementing IDs."""
        id1 = pdf_indexer.index("/path/to/doc1.pdf")
        id2 = pdf_indexer.index("/path/to/doc2.pdf")
        id3 = pdf_indexer.index("/path/to/doc3.pdf")

        assert id1 == 1
        assert id2 == 2
        assert id3 == 3

    def test_index_emits_event(self, pdf_indexer):
        """index() should emit a PDF_INDEXED event."""
        pdf_id = pdf_indexer.index(
            "/path/to/research.pdf",
            title="Deep Learning Study",
            authors="Smith, J.; Doe, A.",
            category=PDFCategory.RESEARCH,
            tags="ml,ai",
            page_count=50
        )

        events = pdf_indexer.explain(pdf_id)
        assert len(events) == 1

        event = events[0]
        assert event["event_type"] == PDF_INDEXED
        assert event["payload"]["title"] == "Deep Learning Study"
        assert event["payload"]["category"] == "research"

    def test_index_uses_filename_as_default_title(self, pdf_indexer):
        """index() should use filename as title if not provided."""
        pdf_id = pdf_indexer.index("/path/to/my_document.pdf")
        pdf = pdf_indexer.get(pdf_id)

        assert pdf["title"] == "my_document"

    def test_index_with_all_fields(self, pdf_indexer):
        """index() should store all provided fields."""
        pdf_id = pdf_indexer.index(
            "/docs/paper.pdf",
            title="Research Paper",
            authors="Author One, Author Two",
            category=PDFCategory.ARTICLE,
            tags="research,important",
            page_count=25
        )

        pdf = pdf_indexer.get(pdf_id)
        assert pdf["file_path"] == "/docs/paper.pdf"
        assert pdf["title"] == "Research Paper"
        assert pdf["authors"] == "Author One, Author Two"
        assert pdf["category"] == "article"
        assert pdf["tags"] == "research,important"
        assert pdf["page_count"] == 25


class TestPDFProjection:
    """Tests for PDF state projection from events."""

    def test_get_pdf_projects_state(self, pdf_indexer):
        """get() should project PDF state from events."""
        pdf_id = pdf_indexer.index("/path/to/doc.pdf", "Test Doc", "Author A", PDFCategory.BOOK)

        pdf = pdf_indexer.get(pdf_id)
        assert pdf["id"] == pdf_id
        assert pdf["title"] == "Test Doc"
        assert pdf["authors"] == "Author A"
        assert pdf["category"] == "book"
        assert pdf["archived"] is False

    def test_get_nonexistent_pdf(self, pdf_indexer):
        """get() should return None for nonexistent PDF."""
        pdf = pdf_indexer.get(999)
        assert pdf is None

    def test_update_title_updates_projection(self, pdf_indexer):
        """update() should update the projected title."""
        pdf_id = pdf_indexer.index("/path/doc.pdf", title="Original Title")
        pdf_indexer.update(pdf_id, title="New Title")

        pdf = pdf_indexer.get(pdf_id)
        assert pdf["title"] == "New Title"

    def test_update_multiple_fields(self, pdf_indexer):
        """update() should update multiple fields."""
        pdf_id = pdf_indexer.index("/path/doc.pdf")
        pdf_indexer.update(pdf_id, authors="New Authors", page_count=100)

        pdf = pdf_indexer.get(pdf_id)
        assert pdf["authors"] == "New Authors"
        assert pdf["page_count"] == 100


class TestPDFTagging:
    """Tests for PDF tagging."""

    def test_tag_sets_tags(self, pdf_indexer):
        """tag() should set tags on a PDF."""
        pdf_id = pdf_indexer.index("/path/doc.pdf")
        pdf_indexer.tag(pdf_id, "important,research,todo")

        pdf = pdf_indexer.get(pdf_id)
        assert pdf["tags"] == "important,research,todo"

    def test_tag_replaces_previous_tags(self, pdf_indexer):
        """tag() should replace previous tags."""
        pdf_id = pdf_indexer.index("/path/doc.pdf", tags="old,tags")
        pdf_indexer.tag(pdf_id, "new,tags")

        pdf = pdf_indexer.get(pdf_id)
        assert pdf["tags"] == "new,tags"

    def test_tag_nonexistent_pdf_returns_false(self, pdf_indexer):
        """tag() should return False for nonexistent PDF."""
        result = pdf_indexer.tag(999, "tag")
        assert result is False


class TestPDFNotes:
    """Tests for PDF notes."""

    def test_add_note(self, pdf_indexer):
        """add_note() should add a note to a PDF."""
        pdf_id = pdf_indexer.index("/path/doc.pdf")
        pdf_indexer.add_note(pdf_id, "This is an important section on page 5.")

        pdf = pdf_indexer.get(pdf_id)
        assert "important section on page 5" in pdf["notes"]

    def test_add_multiple_notes(self, pdf_indexer):
        """add_note() should concatenate multiple notes."""
        pdf_id = pdf_indexer.index("/path/doc.pdf")
        pdf_indexer.add_note(pdf_id, "First note")
        pdf_indexer.add_note(pdf_id, "Second note")

        pdf = pdf_indexer.get(pdf_id)
        assert "First note" in pdf["notes"]
        assert "Second note" in pdf["notes"]

    def test_add_note_nonexistent_pdf_returns_false(self, pdf_indexer):
        """add_note() should return False for nonexistent PDF."""
        result = pdf_indexer.add_note(999, "note")
        assert result is False


class TestPDFArchive:
    """Tests for PDF archiving."""

    def test_archive_marks_pdf_archived(self, pdf_indexer):
        """archive() should mark PDF as archived."""
        pdf_id = pdf_indexer.index("/path/doc.pdf")
        result = pdf_indexer.archive(pdf_id)

        assert result is True
        pdf = pdf_indexer.get(pdf_id)
        assert pdf["archived"] is True

    def test_cannot_archive_already_archived(self, pdf_indexer):
        """archive() should return False for already archived PDF."""
        pdf_id = pdf_indexer.index("/path/doc.pdf")
        pdf_indexer.archive(pdf_id)

        result = pdf_indexer.archive(pdf_id)
        assert result is False

    def test_cannot_update_archived_pdf(self, pdf_indexer):
        """update() should return False for archived PDF."""
        pdf_id = pdf_indexer.index("/path/doc.pdf")
        pdf_indexer.archive(pdf_id)

        result = pdf_indexer.update(pdf_id, title="New Title")
        assert result is False

    def test_cannot_tag_archived_pdf(self, pdf_indexer):
        """tag() should return False for archived PDF."""
        pdf_id = pdf_indexer.index("/path/doc.pdf")
        pdf_indexer.archive(pdf_id)

        result = pdf_indexer.tag(pdf_id, "new-tag")
        assert result is False

    def test_cannot_add_note_to_archived_pdf(self, pdf_indexer):
        """add_note() should return False for archived PDF."""
        pdf_id = pdf_indexer.index("/path/doc.pdf")
        pdf_indexer.archive(pdf_id)

        result = pdf_indexer.add_note(pdf_id, "note")
        assert result is False


class TestPDFList:
    """Tests for listing PDFs."""

    def test_list_all_pdfs(self, pdf_indexer):
        """list_pdfs() should return all PDFs."""
        pdf_indexer.index("/doc1.pdf")
        pdf_indexer.index("/doc2.pdf")
        pdf_indexer.index("/doc3.pdf")

        pdfs = pdf_indexer.list_pdfs()
        assert len(pdfs) == 3

    def test_list_filter_by_category(self, pdf_indexer):
        """list_pdfs(category=X) should filter by category."""
        pdf_indexer.index("/research1.pdf", category=PDFCategory.RESEARCH)
        pdf_indexer.index("/book1.pdf", category=PDFCategory.BOOK)
        pdf_indexer.index("/research2.pdf", category=PDFCategory.RESEARCH)

        pdfs = pdf_indexer.list_pdfs(category=PDFCategory.RESEARCH)
        assert len(pdfs) == 2
        assert all(p["category"] == "research" for p in pdfs)

    def test_list_filter_by_tag(self, pdf_indexer):
        """list_pdfs(tag=X) should filter by tag."""
        id1 = pdf_indexer.index("/doc1.pdf")
        id2 = pdf_indexer.index("/doc2.pdf")
        pdf_indexer.index("/doc3.pdf")

        pdf_indexer.tag(id1, "important,ml")
        pdf_indexer.tag(id2, "important,research")

        pdfs = pdf_indexer.list_pdfs(tag="important")
        assert len(pdfs) == 2

    def test_list_excludes_archived_by_default(self, pdf_indexer):
        """list_pdfs() should exclude archived PDFs by default."""
        id1 = pdf_indexer.index("/doc1.pdf")
        pdf_indexer.index("/doc2.pdf")
        pdf_indexer.archive(id1)

        pdfs = pdf_indexer.list_pdfs()
        assert len(pdfs) == 1

    def test_list_includes_archived_when_requested(self, pdf_indexer):
        """list_pdfs(include_archived=True) should include archived PDFs."""
        id1 = pdf_indexer.index("/doc1.pdf")
        pdf_indexer.index("/doc2.pdf")
        pdf_indexer.archive(id1)

        pdfs = pdf_indexer.list_pdfs(include_archived=True)
        assert len(pdfs) == 2

    def test_list_empty(self, pdf_indexer):
        """list_pdfs() should return empty list when no PDFs."""
        pdfs = pdf_indexer.list_pdfs()
        assert pdfs == []


class TestPDFSearch:
    """Tests for PDF search."""

    def test_search_by_title(self, pdf_indexer):
        """search() should find PDFs by title."""
        pdf_indexer.index("/doc1.pdf", title="Machine Learning Basics")
        pdf_indexer.index("/doc2.pdf", title="Deep Learning")
        pdf_indexer.index("/doc3.pdf", title="Python Programming")

        results = pdf_indexer.search("learning")
        assert len(results) == 2

    def test_search_by_authors(self, pdf_indexer):
        """search() should find PDFs by authors."""
        pdf_indexer.index("/doc1.pdf", authors="John Smith")
        pdf_indexer.index("/doc2.pdf", authors="Jane Doe")

        results = pdf_indexer.search("smith")
        assert len(results) == 1
        assert results[0]["authors"] == "John Smith"

    def test_search_by_notes(self, pdf_indexer):
        """search() should find PDFs by notes."""
        id1 = pdf_indexer.index("/doc1.pdf")
        pdf_indexer.add_note(id1, "Contains information about neural networks")
        pdf_indexer.index("/doc2.pdf")

        results = pdf_indexer.search("neural")
        assert len(results) == 1

    def test_search_case_insensitive(self, pdf_indexer):
        """search() should be case-insensitive."""
        pdf_indexer.index("/doc.pdf", title="MACHINE LEARNING")

        results = pdf_indexer.search("machine")
        assert len(results) == 1

    def test_search_excludes_archived(self, pdf_indexer):
        """search() should exclude archived PDFs by default."""
        id1 = pdf_indexer.index("/doc1.pdf", title="Machine Learning")
        pdf_indexer.index("/doc2.pdf", title="Deep Learning")
        pdf_indexer.archive(id1)

        results = pdf_indexer.search("learning")
        assert len(results) == 1


class TestPDFExplain:
    """Tests for PDF event history (audit trail)."""

    def test_explain_returns_all_events(self, pdf_indexer):
        """explain() should return all events for a PDF."""
        pdf_id = pdf_indexer.index("/doc.pdf")
        pdf_indexer.update(pdf_id, title="Updated Title")
        pdf_indexer.tag(pdf_id, "important")
        pdf_indexer.add_note(pdf_id, "A note")

        events = pdf_indexer.explain(pdf_id)
        assert len(events) == 4

        assert events[0]["event_type"] == PDF_INDEXED
        assert events[1]["event_type"] == PDF_UPDATED
        assert events[2]["event_type"] == PDF_TAGGED
        assert events[3]["event_type"] == PDF_NOTE_ADDED

    def test_explain_empty_for_nonexistent(self, pdf_indexer):
        """explain() should return empty list for nonexistent PDF."""
        events = pdf_indexer.explain(999)
        assert events == []


class TestEventSpineInvariant:
    """Tests verifying the Event Spine invariant is maintained."""

    def test_events_are_canonical(self, temp_db):
        """Events table should be the only source of truth."""
        event_store = EventStore(db=temp_db)
        indexer1 = PDFIndexer(db=temp_db, event_store=event_store)

        # Create and update with indexer1
        pdf_id = indexer1.index("/path/research.pdf", title="Research Paper", category=PDFCategory.RESEARCH)
        indexer1.update(pdf_id, authors="Test Author")
        indexer1.tag(pdf_id, "important,ml")
        indexer1.add_note(pdf_id, "Key findings on page 10")

        # Create new indexer instance (simulates restart)
        indexer2 = PDFIndexer(db=temp_db, event_store=event_store)

        # Should project same state from events
        pdf = indexer2.get(pdf_id)
        assert pdf["title"] == "Research Paper"
        assert pdf["authors"] == "Test Author"
        assert pdf["category"] == "research"
        assert pdf["tags"] == "important,ml"
        assert "Key findings on page 10" in pdf["notes"]
