"""
Tests for the Note Manager (KNOW-002).

Tests the Notes-as-projection pattern: state derived from events only.
"""

import pytest
from pathlib import Path
import tempfile

from modules.core.database import Database
from modules.core.event_store import EventStore
from modules.knowledge.note_manager import (
    NoteManager,
    NOTE_CREATED,
    NOTE_UPDATED,
    NOTE_ARCHIVED,
    NOTE_TAGGED,
)


@pytest.fixture
def note_manager(temp_db):
    """Create a note manager with a temporary database."""
    event_store = EventStore(db=temp_db)
    return NoteManager(db=temp_db, event_store=event_store)


class TestNoteCreate:
    """Tests for note creation."""

    def test_create_returns_note_id(self, note_manager):
        """create() should return the note ID."""
        note_id = note_manager.create("My First Note")
        assert note_id == 1

    def test_create_multiple_notes(self, note_manager):
        """create() should return incrementing IDs."""
        id1 = note_manager.create("Note 1")
        id2 = note_manager.create("Note 2")
        id3 = note_manager.create("Note 3")

        assert id1 == 1
        assert id2 == 2
        assert id3 == 3

    def test_create_emits_event(self, note_manager):
        """create() should emit a NOTE_CREATED event."""
        note_id = note_manager.create("Test Note", "Some content", ["test", "demo"])

        events = note_manager.explain(note_id)
        assert len(events) == 1

        event = events[0]
        assert event["event_type"] == NOTE_CREATED
        assert event["payload"]["title"] == "Test Note"
        assert event["payload"]["content"] == "Some content"
        assert event["payload"]["tags"] == ["test", "demo"]

    def test_create_with_tags(self, note_manager):
        """create() should store tags correctly."""
        note_id = note_manager.create("Tagged Note", tags=["python", "coding"])
        note = note_manager.get(note_id)

        assert note["tags"] == ["python", "coding"]


class TestNoteProjection:
    """Tests for note state projection from events."""

    def test_get_note_projects_state(self, note_manager):
        """get() should project note state from events."""
        note_id = note_manager.create("Test Note", "Content here")

        note = note_manager.get(note_id)
        assert note["id"] == note_id
        assert note["title"] == "Test Note"
        assert note["content"] == "Content here"
        assert note["archived"] is False

    def test_get_nonexistent_note(self, note_manager):
        """get() should return None for nonexistent note."""
        note = note_manager.get(999)
        assert note is None

    def test_update_title_updates_projection(self, note_manager):
        """update() should update the projected title."""
        note_id = note_manager.create("Original Title")
        note_manager.update(note_id, title="New Title")

        note = note_manager.get(note_id)
        assert note["title"] == "New Title"

    def test_update_content_updates_projection(self, note_manager):
        """update() should update the projected content."""
        note_id = note_manager.create("Note", "Original content")
        note_manager.update(note_id, content="Updated content")

        note = note_manager.get(note_id)
        assert note["content"] == "Updated content"

    def test_multiple_updates_project_latest(self, note_manager):
        """Multiple updates should project the latest values."""
        note_id = note_manager.create("Note", "v1")
        note_manager.update(note_id, content="v2")
        note_manager.update(note_id, content="v3")
        note_manager.update(note_id, title="Final Title")

        note = note_manager.get(note_id)
        assert note["title"] == "Final Title"
        assert note["content"] == "v3"


class TestNoteArchive:
    """Tests for note archiving."""

    def test_archive_sets_archived_flag(self, note_manager):
        """archive() should set the archived flag."""
        note_id = note_manager.create("To Archive")
        result = note_manager.archive(note_id)

        assert result is True
        note = note_manager.get(note_id)
        assert note["archived"] is True

    def test_archive_nonexistent_returns_false(self, note_manager):
        """archive() should return False for nonexistent note."""
        result = note_manager.archive(999)
        assert result is False

    def test_archive_already_archived_returns_false(self, note_manager):
        """archive() should return False for already archived note."""
        note_id = note_manager.create("Note")
        note_manager.archive(note_id)

        result = note_manager.archive(note_id)
        assert result is False


class TestNoteTags:
    """Tests for note tagging."""

    def test_tag_adds_tags(self, note_manager):
        """tag() should add tags to a note."""
        note_id = note_manager.create("Note")
        note_manager.tag(note_id, ["python", "tutorial"])

        note = note_manager.get(note_id)
        assert note["tags"] == ["python", "tutorial"]

    def test_tag_replaces_existing_tags(self, note_manager):
        """tag() should replace existing tags."""
        note_id = note_manager.create("Note", tags=["old"])
        note_manager.tag(note_id, ["new1", "new2"])

        note = note_manager.get(note_id)
        assert note["tags"] == ["new1", "new2"]

    def test_get_tags_returns_unique_tags(self, note_manager):
        """get_tags() should return all unique tags."""
        note_manager.create("Note 1", tags=["python", "coding"])
        note_manager.create("Note 2", tags=["python", "tutorial"])
        note_manager.create("Note 3", tags=["javascript"])

        tags = note_manager.get_tags()
        assert sorted(tags) == ["coding", "javascript", "python", "tutorial"]


class TestNoteList:
    """Tests for listing notes."""

    def test_list_all_notes(self, note_manager):
        """list_notes() should return all non-archived notes."""
        note_manager.create("Note 1")
        note_manager.create("Note 2")
        note_manager.create("Note 3")

        notes = note_manager.list_notes()
        assert len(notes) == 3

    def test_list_excludes_archived_by_default(self, note_manager):
        """list_notes() should exclude archived notes by default."""
        id1 = note_manager.create("Note 1")
        note_manager.create("Note 2")
        note_manager.archive(id1)

        notes = note_manager.list_notes()
        assert len(notes) == 1
        assert notes[0]["title"] == "Note 2"

    def test_list_includes_archived_when_requested(self, note_manager):
        """list_notes(include_archived=True) should include archived."""
        id1 = note_manager.create("Note 1")
        note_manager.create("Note 2")
        note_manager.archive(id1)

        notes = note_manager.list_notes(include_archived=True)
        assert len(notes) == 2

    def test_list_filter_by_tag(self, note_manager):
        """list_notes(tag=X) should filter by tag."""
        note_manager.create("Note 1", tags=["python"])
        note_manager.create("Note 2", tags=["javascript"])
        note_manager.create("Note 3", tags=["python", "coding"])

        notes = note_manager.list_notes(tag="python")
        assert len(notes) == 2
        titles = [n["title"] for n in notes]
        assert "Note 1" in titles
        assert "Note 3" in titles

    def test_list_empty(self, note_manager):
        """list_notes() should return empty list when no notes."""
        notes = note_manager.list_notes()
        assert notes == []


class TestNoteSearch:
    """Tests for note search."""

    def test_search_by_title(self, note_manager):
        """search() should find notes by title."""
        note_manager.create("Python Tutorial")
        note_manager.create("JavaScript Guide")
        note_manager.create("Advanced Python")

        results = note_manager.search("python")
        assert len(results) == 2
        titles = [n["title"] for n in results]
        assert "Python Tutorial" in titles
        assert "Advanced Python" in titles

    def test_search_by_content(self, note_manager):
        """search() should find notes by content."""
        note_manager.create("Note 1", "This is about databases")
        note_manager.create("Note 2", "This is about APIs")
        note_manager.create("Note 3", "Database design patterns")

        results = note_manager.search("database")
        assert len(results) == 2

    def test_search_case_insensitive(self, note_manager):
        """search() should be case insensitive."""
        note_manager.create("PYTHON UPPERCASE")
        note_manager.create("python lowercase")

        results = note_manager.search("Python")
        assert len(results) == 2

    def test_search_no_results(self, note_manager):
        """search() should return empty list when no matches."""
        note_manager.create("Note about X")

        results = note_manager.search("nonexistent")
        assert results == []


class TestNoteExplain:
    """Tests for note event history (audit trail)."""

    def test_explain_returns_all_events(self, note_manager):
        """explain() should return all events for a note."""
        note_id = note_manager.create("Note")
        note_manager.update(note_id, title="Updated Title")
        note_manager.tag(note_id, ["test"])
        note_manager.archive(note_id)

        events = note_manager.explain(note_id)
        assert len(events) == 4

        assert events[0]["event_type"] == NOTE_CREATED
        assert events[1]["event_type"] == NOTE_UPDATED
        assert events[2]["event_type"] == NOTE_TAGGED
        assert events[3]["event_type"] == NOTE_ARCHIVED

    def test_explain_empty_for_nonexistent(self, note_manager):
        """explain() should return empty list for nonexistent note."""
        events = note_manager.explain(999)
        assert events == []


class TestEventSpineInvariant:
    """Tests verifying the Event Spine invariant is maintained."""

    def test_events_are_canonical(self, temp_db):
        """Events table should be the only source of truth."""
        event_store = EventStore(db=temp_db)
        manager1 = NoteManager(db=temp_db, event_store=event_store)

        # Create and update with manager1
        note_id = manager1.create("Test Note", "Original")
        manager1.update(note_id, content="Updated")
        manager1.tag(note_id, ["important"])

        # Create new manager instance (simulates restart)
        manager2 = NoteManager(db=temp_db, event_store=event_store)

        # Should project same state from events
        note = manager2.get(note_id)
        assert note["title"] == "Test Note"
        assert note["content"] == "Updated"
        assert note["tags"] == ["important"]
