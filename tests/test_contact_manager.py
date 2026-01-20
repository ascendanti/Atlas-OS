"""
Tests for the Contact Manager module.
"""

import pytest
from datetime import date, timedelta

from modules.life.contact_manager import ContactManager, ContactCategory


class TestContactManager:
    """Tests for ContactManager class."""

    def test_add_contact(self, temp_db):
        """Test adding a contact."""
        manager = ContactManager(db=temp_db)
        contact_id = manager.add("John", last_name="Doe", email="john@example.com")

        assert contact_id == 1

        contact = manager.get(contact_id)
        assert contact["first_name"] == "John"
        assert contact["last_name"] == "Doe"
        assert contact["email"] == "john@example.com"

    def test_add_contact_with_category(self, temp_db):
        """Test adding a contact with category."""
        manager = ContactManager(db=temp_db)
        contact_id = manager.add("Jane", category=ContactCategory.FAMILY)

        contact = manager.get(contact_id)
        assert contact["category"] == "family"

    def test_list_contacts(self, temp_db):
        """Test listing contacts."""
        manager = ContactManager(db=temp_db)
        manager.add("Alice")
        manager.add("Bob")
        manager.add("Charlie")

        contacts = manager.list()
        assert len(contacts) == 3

    def test_list_contacts_by_category(self, temp_db):
        """Test filtering contacts by category."""
        manager = ContactManager(db=temp_db)
        manager.add("Family Member", category=ContactCategory.FAMILY)
        manager.add("Friend 1", category=ContactCategory.FRIEND)
        manager.add("Friend 2", category=ContactCategory.FRIEND)

        friends = manager.list(category=ContactCategory.FRIEND)
        assert len(friends) == 2

    def test_update_contact(self, temp_db):
        """Test updating a contact."""
        manager = ContactManager(db=temp_db)
        contact_id = manager.add("Original Name")

        manager.update(contact_id, first_name="Updated Name", phone="123-456-7890")

        contact = manager.get(contact_id)
        assert contact["first_name"] == "Updated Name"
        assert contact["phone"] == "123-456-7890"

    def test_delete_contact(self, temp_db):
        """Test deleting a contact."""
        manager = ContactManager(db=temp_db)
        contact_id = manager.add("To Delete")

        result = manager.delete(contact_id)
        assert result is True

        contact = manager.get(contact_id)
        assert contact is None

    def test_search_contacts(self, temp_db):
        """Test searching contacts."""
        manager = ContactManager(db=temp_db)
        manager.add("John", last_name="Smith", email="john@acme.com", company="Acme Inc")
        manager.add("Jane", last_name="Doe")
        manager.add("Bob", last_name="Johnson", company="Acme Inc")

        # Search by name
        results = manager.search("John")
        assert len(results) == 2  # John Smith and Bob Johnson

        # Search by company
        results = manager.search("Acme")
        assert len(results) == 2

    def test_record_contact(self, temp_db):
        """Test recording contact date."""
        manager = ContactManager(db=temp_db)
        contact_id = manager.add("Friend")

        manager.record_contact(contact_id)

        contact = manager.get(contact_id)
        assert contact["last_contact"] == date.today().isoformat()

    def test_upcoming_birthdays(self, temp_db):
        """Test getting upcoming birthdays."""
        manager = ContactManager(db=temp_db)

        # Birthday in 5 days (adjust year to make it upcoming)
        today = date.today()
        upcoming_bday = today + timedelta(days=5)
        upcoming_bday = upcoming_bday.replace(year=1990)  # Set a past year

        past_bday = today - timedelta(days=30)
        past_bday = past_bday.replace(year=1985)

        manager.add("Upcoming Birthday", birthday=upcoming_bday)
        manager.add("Past Birthday", birthday=past_bday)

        upcoming = manager.get_upcoming_birthdays(days=10)
        assert len(upcoming) >= 1
        assert upcoming[0]["first_name"] == "Upcoming Birthday"

    def test_birthdays_this_month(self, temp_db):
        """Test getting birthdays this month."""
        manager = ContactManager(db=temp_db)

        today = date.today()
        this_month_bday = today.replace(day=15, year=1990)
        other_month_bday = (today.replace(day=1) + timedelta(days=45)).replace(year=1990)

        manager.add("This Month", birthday=this_month_bday)
        manager.add("Other Month", birthday=other_month_bday)

        birthdays = manager.get_birthdays_this_month()
        assert any(c["first_name"] == "This Month" for c in birthdays)

    def test_needs_contact(self, temp_db):
        """Test getting contacts that need attention."""
        manager = ContactManager(db=temp_db)

        # Contact from long ago
        contact_id = manager.add("Old Friend", contact_frequency_days=30)
        old_date = date.today() - timedelta(days=60)
        manager.update(contact_id, last_contact=old_date)

        # Recently contacted
        recent_id = manager.add("Recent Friend", contact_frequency_days=30)
        manager.record_contact(recent_id)

        needs_contact = manager.get_needs_contact()
        assert len(needs_contact) == 1
        assert needs_contact[0]["first_name"] == "Old Friend"

    def test_full_name(self, temp_db):
        """Test full name helper."""
        manager = ContactManager(db=temp_db)

        contact_id = manager.add("John", last_name="Doe")
        contact = manager.get(contact_id)
        assert manager.full_name(contact) == "John Doe"

        contact_id2 = manager.add("Madonna")
        contact2 = manager.get(contact_id2)
        assert manager.full_name(contact2) == "Madonna"

    def test_count_contacts(self, temp_db):
        """Test counting contacts."""
        manager = ContactManager(db=temp_db)
        manager.add("Friend 1", category=ContactCategory.FRIEND)
        manager.add("Friend 2", category=ContactCategory.FRIEND)
        manager.add("Family", category=ContactCategory.FAMILY)

        total = manager.count()
        friends = manager.count(ContactCategory.FRIEND)

        assert total == 3
        assert friends == 2
