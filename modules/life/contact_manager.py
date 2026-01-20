"""
Atlas Personal OS - Contact Manager (Modern Rolodex)

A personal contact management system with birthday reminders,
last contact tracking, and relationship management.
"""

from __future__ import annotations

from datetime import datetime, date
from typing import Optional
from enum import Enum

from modules.core.database import Database, get_database


class ContactCategory(Enum):
    """Contact relationship categories."""
    FAMILY = "family"
    FRIEND = "friend"
    COLLEAGUE = "colleague"
    PROFESSIONAL = "professional"
    ACQUAINTANCE = "acquaintance"
    OTHER = "other"


class ContactManager:
    """Personal contact management system."""

    TABLE_NAME = "contacts"
    SCHEMA = """
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT,
        email TEXT,
        phone TEXT,
        address TEXT,
        city TEXT,
        country TEXT,
        birthday DATE,
        category TEXT DEFAULT 'other',
        company TEXT,
        job_title TEXT,
        notes TEXT,
        last_contact DATE,
        contact_frequency_days INTEGER DEFAULT 90,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    """

    def __init__(self, db: Optional[Database] = None):
        """Initialize contact manager with database."""
        self.db = db or get_database()
        self._ensure_table()

    def _ensure_table(self) -> None:
        """Create contacts table if it doesn't exist."""
        self.db.create_table(self.TABLE_NAME, self.SCHEMA)

    def add(
        self,
        first_name: str,
        last_name: str = "",
        email: str = "",
        phone: str = "",
        address: str = "",
        city: str = "",
        country: str = "",
        birthday: Optional[date] = None,
        category: ContactCategory = ContactCategory.OTHER,
        company: str = "",
        job_title: str = "",
        notes: str = "",
        contact_frequency_days: int = 90
    ) -> int:
        """
        Add a new contact.

        Returns:
            ID of the created contact
        """
        data = {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "phone": phone,
            "address": address,
            "city": city,
            "country": country,
            "birthday": birthday.isoformat() if birthday else None,
            "category": category.value,
            "company": company,
            "job_title": job_title,
            "notes": notes,
            "contact_frequency_days": contact_frequency_days,
        }
        return self.db.insert(self.TABLE_NAME, data)

    def get(self, contact_id: int) -> Optional[dict]:
        """Get a contact by ID."""
        row = self.db.fetchone(
            f"SELECT * FROM {self.TABLE_NAME} WHERE id = ?",
            (contact_id,)
        )
        return dict(row) if row else None

    def list(
        self,
        category: Optional[ContactCategory] = None,
        limit: int = 100
    ) -> list[dict]:
        """List contacts with optional category filter."""
        if category:
            rows = self.db.fetchall(
                f"SELECT * FROM {self.TABLE_NAME} WHERE category = ? ORDER BY first_name, last_name LIMIT ?",
                (category.value, limit)
            )
        else:
            rows = self.db.fetchall(
                f"SELECT * FROM {self.TABLE_NAME} ORDER BY first_name, last_name LIMIT ?",
                (limit,)
            )
        return [dict(row) for row in rows]

    def update(self, contact_id: int, **kwargs) -> bool:
        """Update a contact."""
        if not kwargs:
            return False

        if "category" in kwargs and isinstance(kwargs["category"], ContactCategory):
            kwargs["category"] = kwargs["category"].value
        if "birthday" in kwargs and isinstance(kwargs["birthday"], date):
            kwargs["birthday"] = kwargs["birthday"].isoformat()
        if "last_contact" in kwargs and isinstance(kwargs["last_contact"], date):
            kwargs["last_contact"] = kwargs["last_contact"].isoformat()

        kwargs["updated_at"] = datetime.now().isoformat()

        rows_updated = self.db.update(
            self.TABLE_NAME,
            kwargs,
            "id = ?",
            (contact_id,)
        )
        return rows_updated > 0

    def delete(self, contact_id: int) -> bool:
        """Delete a contact."""
        rows_deleted = self.db.delete(
            self.TABLE_NAME,
            "id = ?",
            (contact_id,)
        )
        return rows_deleted > 0

    def search(self, query: str) -> list[dict]:
        """Search contacts by name, email, or company."""
        sql = f"""
            SELECT * FROM {self.TABLE_NAME}
            WHERE first_name LIKE ? OR last_name LIKE ?
                OR email LIKE ? OR company LIKE ?
            ORDER BY first_name, last_name
        """
        pattern = f"%{query}%"
        rows = self.db.fetchall(sql, (pattern, pattern, pattern, pattern))
        return [dict(row) for row in rows]

    def record_contact(self, contact_id: int, contact_date: Optional[date] = None) -> bool:
        """Record that you contacted someone."""
        if contact_date is None:
            contact_date = date.today()
        return self.update(contact_id, last_contact=contact_date)

    def get_birthdays_this_month(self) -> list[dict]:
        """Get contacts with birthdays this month."""
        current_month = date.today().month
        rows = self.db.fetchall(
            f"""SELECT * FROM {self.TABLE_NAME}
                WHERE CAST(strftime('%m', birthday) AS INTEGER) = ?
                ORDER BY CAST(strftime('%d', birthday) AS INTEGER)""",
            (current_month,)
        )
        return [dict(row) for row in rows]

    def get_upcoming_birthdays(self, days: int = 30) -> list[dict]:
        """Get contacts with birthdays in the next N days."""
        today = date.today()
        rows = self.db.fetchall(f"SELECT * FROM {self.TABLE_NAME} WHERE birthday IS NOT NULL")

        upcoming = []
        for row in rows:
            contact = dict(row)
            if contact["birthday"]:
                bday = date.fromisoformat(contact["birthday"])
                this_year_bday = bday.replace(year=today.year)
                if this_year_bday < today:
                    this_year_bday = this_year_bday.replace(year=today.year + 1)
                days_until = (this_year_bday - today).days
                if 0 <= days_until <= days:
                    contact["days_until_birthday"] = days_until
                    upcoming.append(contact)

        return sorted(upcoming, key=lambda x: x["days_until_birthday"])

    def get_needs_contact(self) -> list[dict]:
        """Get contacts you haven't reached out to in a while."""
        today = date.today()
        rows = self.db.fetchall(
            f"SELECT * FROM {self.TABLE_NAME} WHERE last_contact IS NOT NULL"
        )

        needs_contact = []
        for row in rows:
            contact = dict(row)
            last = date.fromisoformat(contact["last_contact"])
            days_since = (today - last).days
            if days_since >= contact["contact_frequency_days"]:
                contact["days_since_contact"] = days_since
                needs_contact.append(contact)

        return sorted(needs_contact, key=lambda x: x["days_since_contact"], reverse=True)

    def count(self, category: Optional[ContactCategory] = None) -> int:
        """Count contacts."""
        if category:
            row = self.db.fetchone(
                f"SELECT COUNT(*) as count FROM {self.TABLE_NAME} WHERE category = ?",
                (category.value,)
            )
        else:
            row = self.db.fetchone(f"SELECT COUNT(*) as count FROM {self.TABLE_NAME}")
        return row["count"] if row else 0

    def full_name(self, contact: dict) -> str:
        """Get full name from contact dict."""
        if contact["last_name"]:
            return f"{contact['first_name']} {contact['last_name']}"
        return contact["first_name"]
