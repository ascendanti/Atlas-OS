"""
Tests for the Publication Tracker (CAR-001).

Tests the Publication-as-projection pattern: state derived from events only.
"""

import pytest

from modules.core.database import Database
from modules.core.event_store import EventStore
from modules.career.publication_tracker import (
    PublicationTracker,
    VenueType,
    PubStatus,
    PUB_CREATED,
    PUB_UPDATED,
    PUB_SUBMITTED,
    PUB_ACCEPTED,
    PUB_REJECTED,
    PUB_PUBLISHED,
)


@pytest.fixture
def pub_tracker(temp_db):
    """Create a publication tracker with a temporary database."""
    event_store = EventStore(db=temp_db)
    return PublicationTracker(db=temp_db, event_store=event_store)


class TestPublicationAdd:
    """Tests for publication creation."""

    def test_add_returns_pub_id(self, pub_tracker):
        """add() should return the publication ID."""
        pub_id = pub_tracker.add("My Research Paper")
        assert pub_id == 1

    def test_add_multiple_publications(self, pub_tracker):
        """add() should return incrementing IDs."""
        id1 = pub_tracker.add("Paper 1")
        id2 = pub_tracker.add("Paper 2")
        id3 = pub_tracker.add("Paper 3")

        assert id1 == 1
        assert id2 == 2
        assert id3 == 3

    def test_add_emits_event(self, pub_tracker):
        """add() should emit a PUB_CREATED event."""
        pub_id = pub_tracker.add(
            "Deep Learning Study",
            authors="Smith, J.; Doe, A.",
            venue=VenueType.JOURNAL,
            abstract="A study on deep learning.",
            tags="ml,ai"
        )

        events = pub_tracker.explain(pub_id)
        assert len(events) == 1

        event = events[0]
        assert event["event_type"] == PUB_CREATED
        assert event["payload"]["title"] == "Deep Learning Study"
        assert event["payload"]["venue"] == "journal"

    def test_add_with_defaults(self, pub_tracker):
        """add() should use default values."""
        pub_id = pub_tracker.add("Simple Paper")
        pub = pub_tracker.get(pub_id)

        assert pub["status"] == "draft"
        assert pub["authors"] == ""
        assert pub["venue"] == "other"


class TestPublicationProjection:
    """Tests for publication state projection from events."""

    def test_get_publication_projects_state(self, pub_tracker):
        """get() should project publication state from events."""
        pub_id = pub_tracker.add("Test Paper", "Author A", VenueType.CONFERENCE)

        pub = pub_tracker.get(pub_id)
        assert pub["id"] == pub_id
        assert pub["title"] == "Test Paper"
        assert pub["authors"] == "Author A"
        assert pub["venue"] == "conference"
        assert pub["status"] == "draft"

    def test_get_nonexistent_publication(self, pub_tracker):
        """get() should return None for nonexistent publication."""
        pub = pub_tracker.get(999)
        assert pub is None

    def test_update_title_updates_projection(self, pub_tracker):
        """update() should update the projected title."""
        pub_id = pub_tracker.add("Original Title")
        pub_tracker.update(pub_id, title="New Title")

        pub = pub_tracker.get(pub_id)
        assert pub["title"] == "New Title"

    def test_update_multiple_fields(self, pub_tracker):
        """update() should update multiple fields."""
        pub_id = pub_tracker.add("Paper")
        pub_tracker.update(pub_id, authors="New Authors", abstract="New abstract")

        pub = pub_tracker.get(pub_id)
        assert pub["authors"] == "New Authors"
        assert pub["abstract"] == "New abstract"


class TestPublicationWorkflow:
    """Tests for publication submission workflow."""

    def test_workflow_draft_to_submitted(self, pub_tracker):
        """submit() should transition from draft to submitted."""
        pub_id = pub_tracker.add("Paper")
        result = pub_tracker.submit(pub_id)

        assert result is True
        pub = pub_tracker.get(pub_id)
        assert pub["status"] == "submitted"
        assert pub["submission_date"] is not None

    def test_workflow_submitted_to_accepted(self, pub_tracker):
        """accept() should transition from submitted to accepted."""
        pub_id = pub_tracker.add("Paper")
        pub_tracker.submit(pub_id)
        result = pub_tracker.accept(pub_id)

        assert result is True
        pub = pub_tracker.get(pub_id)
        assert pub["status"] == "accepted"
        assert pub["acceptance_date"] is not None

    def test_workflow_submitted_to_rejected(self, pub_tracker):
        """reject() should transition from submitted to rejected."""
        pub_id = pub_tracker.add("Paper")
        pub_tracker.submit(pub_id)
        result = pub_tracker.reject(pub_id)

        assert result is True
        pub = pub_tracker.get(pub_id)
        assert pub["status"] == "rejected"
        assert pub["rejection_date"] is not None

    def test_workflow_accepted_to_published(self, pub_tracker):
        """publish() should transition from accepted to published."""
        pub_id = pub_tracker.add("Paper")
        pub_tracker.submit(pub_id)
        pub_tracker.accept(pub_id)
        result = pub_tracker.publish(pub_id, doi="10.1234/test", url="https://example.com/paper")

        assert result is True
        pub = pub_tracker.get(pub_id)
        assert pub["status"] == "published"
        assert pub["publication_date"] is not None
        assert pub["doi"] == "10.1234/test"
        assert pub["url"] == "https://example.com/paper"

    def test_full_workflow_to_published(self, pub_tracker):
        """Publication should transition through full workflow."""
        pub_id = pub_tracker.add("Research Paper", venue=VenueType.JOURNAL)

        assert pub_tracker.get(pub_id)["status"] == "draft"

        pub_tracker.submit(pub_id)
        assert pub_tracker.get(pub_id)["status"] == "submitted"

        pub_tracker.accept(pub_id)
        assert pub_tracker.get(pub_id)["status"] == "accepted"

        pub_tracker.publish(pub_id, doi="10.1234/paper")
        assert pub_tracker.get(pub_id)["status"] == "published"

    def test_cannot_skip_workflow_steps(self, pub_tracker):
        """Workflow should not allow skipping steps."""
        pub_id = pub_tracker.add("Paper")

        # Cannot accept without submitting
        assert pub_tracker.accept(pub_id) is False
        assert pub_tracker.get(pub_id)["status"] == "draft"

        # Cannot publish without accepting
        pub_tracker.submit(pub_id)
        assert pub_tracker.publish(pub_id) is False

    def test_cannot_accept_rejected(self, pub_tracker):
        """Cannot accept a rejected publication."""
        pub_id = pub_tracker.add("Paper")
        pub_tracker.submit(pub_id)
        pub_tracker.reject(pub_id)

        assert pub_tracker.accept(pub_id) is False

    def test_nonexistent_publication_workflow(self, pub_tracker):
        """Workflow methods should return False for nonexistent publication."""
        assert pub_tracker.submit(999) is False
        assert pub_tracker.accept(999) is False
        assert pub_tracker.reject(999) is False
        assert pub_tracker.publish(999) is False


class TestPublicationList:
    """Tests for listing publications."""

    def test_list_all_publications(self, pub_tracker):
        """list_publications() should return all publications."""
        pub_tracker.add("Paper 1")
        pub_tracker.add("Paper 2")
        pub_tracker.add("Paper 3")

        pubs = pub_tracker.list_publications()
        assert len(pubs) == 3

    def test_list_filter_by_status(self, pub_tracker):
        """list_publications(status=X) should filter by status."""
        id1 = pub_tracker.add("Paper 1")
        id2 = pub_tracker.add("Paper 2")
        pub_tracker.add("Paper 3")

        pub_tracker.submit(id1)
        pub_tracker.submit(id2)

        pubs = pub_tracker.list_publications(status=PubStatus.SUBMITTED)
        assert len(pubs) == 2
        assert all(p["status"] == "submitted" for p in pubs)

    def test_list_filter_by_venue(self, pub_tracker):
        """list_publications(venue=X) should filter by venue."""
        pub_tracker.add("Journal Paper", venue=VenueType.JOURNAL)
        pub_tracker.add("Conference Paper", venue=VenueType.CONFERENCE)
        pub_tracker.add("Another Journal", venue=VenueType.JOURNAL)

        pubs = pub_tracker.list_publications(venue=VenueType.JOURNAL)
        assert len(pubs) == 2
        assert all(p["venue"] == "journal" for p in pubs)

    def test_list_empty(self, pub_tracker):
        """list_publications() should return empty list when no publications."""
        pubs = pub_tracker.list_publications()
        assert pubs == []


class TestPublicationExplain:
    """Tests for publication event history (audit trail)."""

    def test_explain_returns_all_events(self, pub_tracker):
        """explain() should return all events for a publication."""
        pub_id = pub_tracker.add("Paper")
        pub_tracker.update(pub_id, title="Updated Paper")
        pub_tracker.submit(pub_id)
        pub_tracker.accept(pub_id)

        events = pub_tracker.explain(pub_id)
        assert len(events) == 4

        assert events[0]["event_type"] == PUB_CREATED
        assert events[1]["event_type"] == PUB_UPDATED
        assert events[2]["event_type"] == PUB_SUBMITTED
        assert events[3]["event_type"] == PUB_ACCEPTED

    def test_explain_empty_for_nonexistent(self, pub_tracker):
        """explain() should return empty list for nonexistent publication."""
        events = pub_tracker.explain(999)
        assert events == []


class TestEventSpineInvariant:
    """Tests verifying the Event Spine invariant is maintained."""

    def test_events_are_canonical(self, temp_db):
        """Events table should be the only source of truth."""
        event_store = EventStore(db=temp_db)
        tracker1 = PublicationTracker(db=temp_db, event_store=event_store)

        # Create and update with tracker1
        pub_id = tracker1.add("Test Paper", venue=VenueType.JOURNAL)
        tracker1.update(pub_id, authors="Test Author")
        tracker1.submit(pub_id)

        # Create new tracker instance (simulates restart)
        tracker2 = PublicationTracker(db=temp_db, event_store=event_store)

        # Should project same state from events
        pub = tracker2.get(pub_id)
        assert pub["title"] == "Test Paper"
        assert pub["authors"] == "Test Author"
        assert pub["venue"] == "journal"
        assert pub["status"] == "submitted"
        assert pub["submission_date"] is not None
