"""
Tests for CV/Resume Manager (CAR-002).
"""

import pytest

from modules.career.cv_manager import CVManager, EntryType
from modules.core.event_store import EventStore


def test_add_and_get_entry_normalizes(temp_db):
    event_store = EventStore(db=temp_db)
    manager = CVManager(db=temp_db, event_store=event_store)

    entry_id = manager.add(
        entry_type=EntryType.EXPERIENCE,
        title="Backend Engineer",
        organization="Atlas Labs",
        description="Built core services",
        start_date="Jan 5, 2020",
        end_date="2021-02-01",
        tags=["Python", "Infra", "python"],
        highlights=["Led migration", "Reduced costs"]
    )

    entry = manager.get(entry_id)
    assert entry["start_date"] == "2020-01-05"
    assert entry["end_date"] == "2021-02-01"
    assert entry["tags"] == "Python, Infra"
    assert "Led migration" in entry["highlights"]


def test_update_validates_date_range(temp_db):
    event_store = EventStore(db=temp_db)
    manager = CVManager(db=temp_db, event_store=event_store)

    entry_id = manager.add(
        entry_type=EntryType.PROJECT,
        title="Apollo",
        start_date="2020-01-01",
        end_date="2020-12-31"
    )

    with pytest.raises(ValueError):
        manager.update(entry_id, end_date="2019-12-31")


def test_list_filters_and_export(temp_db):
    event_store = EventStore(db=temp_db)
    manager = CVManager(db=temp_db, event_store=event_store)

    manager.add(
        entry_type=EntryType.EXPERIENCE,
        title="Data Scientist",
        organization="Nova",
        tags="ml, ai",
        start_date="2021-01-01",
        end_date="2022-01-01"
    )
    manager.add(
        entry_type=EntryType.PROJECT,
        title="Forecasting Engine",
        tags="ml, python",
        start_date="2023-02-01"
    )

    ml_entries = manager.list_entries(tag="ml")
    assert len(ml_entries) == 2

    search_results = manager.list_entries(query="Nova")
    assert len(search_results) == 1

    recent_entries = manager.list_entries(start_after="2022-06-01")
    assert len(recent_entries) == 1

    markdown = manager.export_markdown()
    assert "## Work Experience" in markdown
    assert "Forecasting Engine" in markdown
