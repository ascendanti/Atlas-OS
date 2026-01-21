"""
Atlas Personal OS - Job Application Tracker (CAR-003)

Event-sourced job application tracking:
- Track job applications and their status
- Store company, role, salary, and contact info
- Status workflow: saved → applied → interviewing → offered → accepted/rejected
- Track interview stages and notes
- Deadline and follow-up reminders
"""

from __future__ import annotations
from datetime import datetime, date
from typing import Optional, List
from enum import Enum

from modules.core.database import Database, get_database
from modules.core.event_store import EventStore, get_event_store


# Event Types
APPLICATION_CREATED = "APPLICATION_CREATED"
APPLICATION_UPDATED = "APPLICATION_UPDATED"
APPLICATION_STATUS_CHANGED = "APPLICATION_STATUS_CHANGED"
INTERVIEW_SCHEDULED = "INTERVIEW_SCHEDULED"
INTERVIEW_COMPLETED = "INTERVIEW_COMPLETED"
NOTE_ADDED = "NOTE_ADDED"
OFFER_RECEIVED = "OFFER_RECEIVED"
APPLICATION_ARCHIVED = "APPLICATION_ARCHIVED"


class ApplicationStatus(Enum):
    """Job application statuses."""
    SAVED = "saved"           # Saved for later
    APPLIED = "applied"       # Application submitted
    INTERVIEWING = "interviewing"  # In interview process
    OFFERED = "offered"       # Received offer
    ACCEPTED = "accepted"     # Accepted offer
    REJECTED = "rejected"     # Rejected (by company or self)
    WITHDRAWN = "withdrawn"   # Withdrew application
    ARCHIVED = "archived"


class InterviewType(Enum):
    """Types of interviews."""
    PHONE = "phone"
    VIDEO = "video"
    ONSITE = "onsite"
    TECHNICAL = "technical"
    BEHAVIORAL = "behavioral"
    FINAL = "final"


class JobTracker:
    """
    Event-sourced job application tracker.

    Tracks job applications through the entire hiring
    process with interviews, offers, and notes.
    """

    ENTITY_TYPE = "job_application"
    INTERVIEW_ENTITY = "interview"

    def __init__(
        self,
        db: Optional[Database] = None,
        event_store: Optional[EventStore] = None
    ):
        self.db = db or get_database()
        self.event_store = event_store or get_event_store()
        self._next_id = self._compute_next_id()

    def _compute_next_id(self) -> int:
        """Compute next application ID from events."""
        events = self.event_store.query(
            entity_type=self.ENTITY_TYPE,
            event_type=APPLICATION_CREATED
        )
        if not events:
            return 1
        return max(int(e["entity_id"]) for e in events) + 1

    # ========================================================================
    # APPLICATION COMMANDS
    # ========================================================================

    def create(
        self,
        company: str,
        role: str,
        url: str = "",
        salary_min: Optional[int] = None,
        salary_max: Optional[int] = None,
        location: str = "",
        remote: bool = False,
        contact_name: str = "",
        contact_email: str = "",
        notes: str = "",
        deadline: Optional[date] = None,
    ) -> int:
        """
        Create a new job application.

        Args:
            company: Company name
            role: Job title/role
            url: Job posting URL
            salary_min: Minimum salary
            salary_max: Maximum salary
            location: Job location
            remote: Whether remote work is available
            contact_name: Recruiter/contact name
            contact_email: Contact email
            notes: Initial notes
            deadline: Application deadline

        Returns:
            Application ID
        """
        app_id = self._next_id
        self._next_id += 1

        self.event_store.emit(
            event_type=APPLICATION_CREATED,
            entity_type=self.ENTITY_TYPE,
            entity_id=app_id,
            payload={
                "company": company,
                "role": role,
                "url": url,
                "salary_min": salary_min,
                "salary_max": salary_max,
                "location": location,
                "remote": remote,
                "contact_name": contact_name,
                "contact_email": contact_email,
                "notes": notes,
                "deadline": deadline.isoformat() if deadline else None,
                "status": ApplicationStatus.SAVED.value,
            }
        )
        return app_id

    def update(
        self,
        app_id: int,
        company: Optional[str] = None,
        role: Optional[str] = None,
        url: Optional[str] = None,
        salary_min: Optional[int] = None,
        salary_max: Optional[int] = None,
        location: Optional[str] = None,
        remote: Optional[bool] = None,
        contact_name: Optional[str] = None,
        contact_email: Optional[str] = None,
        deadline: Optional[date] = None,
    ) -> bool:
        """Update application details."""
        app = self.get(app_id)
        if not app:
            return False

        payload = {}
        for key, val in [
            ("company", company), ("role", role), ("url", url),
            ("salary_min", salary_min), ("salary_max", salary_max),
            ("location", location), ("remote", remote),
            ("contact_name", contact_name), ("contact_email", contact_email),
        ]:
            if val is not None:
                payload[key] = val
        if deadline is not None:
            payload["deadline"] = deadline.isoformat() if deadline else None

        if payload:
            self.event_store.emit(
                event_type=APPLICATION_UPDATED,
                entity_type=self.ENTITY_TYPE,
                entity_id=app_id,
                payload=payload
            )
        return True

    def apply(self, app_id: int, applied_date: Optional[date] = None) -> bool:
        """Mark application as submitted."""
        app = self.get(app_id)
        if not app:
            return False

        self.event_store.emit(
            event_type=APPLICATION_STATUS_CHANGED,
            entity_type=self.ENTITY_TYPE,
            entity_id=app_id,
            payload={
                "status": ApplicationStatus.APPLIED.value,
                "applied_date": (applied_date or date.today()).isoformat(),
            }
        )
        return True

    def set_status(self, app_id: int, status: ApplicationStatus) -> bool:
        """Change application status."""
        app = self.get(app_id)
        if not app:
            return False

        self.event_store.emit(
            event_type=APPLICATION_STATUS_CHANGED,
            entity_type=self.ENTITY_TYPE,
            entity_id=app_id,
            payload={"status": status.value, "previous_status": app["status"]}
        )
        return True

    def add_note(self, app_id: int, note: str) -> bool:
        """Add a note to an application."""
        app = self.get(app_id)
        if not app:
            return False

        self.event_store.emit(
            event_type=NOTE_ADDED,
            entity_type=self.ENTITY_TYPE,
            entity_id=app_id,
            payload={"note": note, "added_at": datetime.now().isoformat()}
        )
        return True

    def archive(self, app_id: int) -> bool:
        """Archive an application."""
        return self.set_status(app_id, ApplicationStatus.ARCHIVED)

    # ========================================================================
    # INTERVIEWS
    # ========================================================================

    def schedule_interview(
        self,
        app_id: int,
        interview_type: InterviewType,
        scheduled_date: date,
        scheduled_time: str = "",
        interviewer: str = "",
        notes: str = "",
    ) -> Optional[int]:
        """Schedule an interview."""
        app = self.get(app_id)
        if not app:
            return None

        # Generate interview ID
        i_events = self.event_store.query(
            entity_type=self.INTERVIEW_ENTITY,
            event_type=INTERVIEW_SCHEDULED
        )
        i_id = max((int(e["entity_id"]) for e in i_events), default=0) + 1

        self.event_store.emit(
            event_type=INTERVIEW_SCHEDULED,
            entity_type=self.INTERVIEW_ENTITY,
            entity_id=i_id,
            payload={
                "app_id": app_id,
                "interview_type": interview_type.value,
                "scheduled_date": scheduled_date.isoformat(),
                "scheduled_time": scheduled_time,
                "interviewer": interviewer,
                "notes": notes,
                "completed": False,
            }
        )

        # Update app status if not already interviewing
        if app["status"] in ["saved", "applied"]:
            self.set_status(app_id, ApplicationStatus.INTERVIEWING)

        return i_id

    def complete_interview(
        self,
        interview_id: int,
        outcome: str = "",
        feedback: str = "",
        next_steps: str = "",
    ) -> bool:
        """Mark an interview as completed with feedback."""
        i = self.get_interview(interview_id)
        if not i:
            return False

        self.event_store.emit(
            event_type=INTERVIEW_COMPLETED,
            entity_type=self.INTERVIEW_ENTITY,
            entity_id=interview_id,
            payload={
                "outcome": outcome,
                "feedback": feedback,
                "next_steps": next_steps,
                "completed_at": datetime.now().isoformat(),
            }
        )
        return True

    def get_interview(self, interview_id: int) -> Optional[dict]:
        """Get interview details."""
        events = self.event_store.explain(self.INTERVIEW_ENTITY, interview_id)
        if not events:
            return None

        state = {
            "id": interview_id,
            "app_id": None,
            "interview_type": "",
            "scheduled_date": None,
            "scheduled_time": "",
            "interviewer": "",
            "notes": "",
            "completed": False,
            "outcome": "",
            "feedback": "",
        }

        for event in events:
            payload = event["payload"]
            if event["event_type"] == INTERVIEW_SCHEDULED:
                state.update({
                    "app_id": payload.get("app_id"),
                    "interview_type": payload.get("interview_type", ""),
                    "scheduled_date": payload.get("scheduled_date"),
                    "scheduled_time": payload.get("scheduled_time", ""),
                    "interviewer": payload.get("interviewer", ""),
                    "notes": payload.get("notes", ""),
                })
            elif event["event_type"] == INTERVIEW_COMPLETED:
                state["completed"] = True
                state["outcome"] = payload.get("outcome", "")
                state["feedback"] = payload.get("feedback", "")

        return state

    def get_interviews(self, app_id: int) -> List[dict]:
        """Get all interviews for an application."""
        i_events = self.event_store.query(
            entity_type=self.INTERVIEW_ENTITY,
            event_type=INTERVIEW_SCHEDULED
        )

        interviews = []
        for event in i_events:
            if event["payload"].get("app_id") == app_id:
                i_id = int(event["entity_id"])
                interview = self.get_interview(i_id)
                if interview:
                    interviews.append(interview)

        # Sort by date
        return sorted(interviews, key=lambda x: x["scheduled_date"] or "")

    # ========================================================================
    # OFFERS
    # ========================================================================

    def record_offer(
        self,
        app_id: int,
        salary: int,
        bonus: int = 0,
        equity: str = "",
        start_date: Optional[date] = None,
        deadline: Optional[date] = None,
        benefits: str = "",
        notes: str = "",
    ) -> bool:
        """Record a job offer."""
        app = self.get(app_id)
        if not app:
            return False

        self.event_store.emit(
            event_type=OFFER_RECEIVED,
            entity_type=self.ENTITY_TYPE,
            entity_id=app_id,
            payload={
                "salary": salary,
                "bonus": bonus,
                "equity": equity,
                "start_date": start_date.isoformat() if start_date else None,
                "deadline": deadline.isoformat() if deadline else None,
                "benefits": benefits,
                "notes": notes,
            }
        )
        self.set_status(app_id, ApplicationStatus.OFFERED)
        return True

    def accept_offer(self, app_id: int) -> bool:
        """Accept an offer."""
        return self.set_status(app_id, ApplicationStatus.ACCEPTED)

    def reject_offer(self, app_id: int, reason: str = "") -> bool:
        """Reject/decline an offer."""
        app = self.get(app_id)
        if not app:
            return False
        if reason:
            self.add_note(app_id, f"Declined offer: {reason}")
        return self.set_status(app_id, ApplicationStatus.REJECTED)

    # ========================================================================
    # PROJECTIONS
    # ========================================================================

    def get(self, app_id: int) -> Optional[dict]:
        """Get application state by projecting from events."""
        events = self.event_store.explain(self.ENTITY_TYPE, app_id)
        if not events:
            return None

        return self._project(app_id, events)

    def _project(self, app_id: int, events: list[dict]) -> dict:
        """Project state from events."""
        state = {
            "id": app_id,
            "company": "",
            "role": "",
            "url": "",
            "salary_min": None,
            "salary_max": None,
            "location": "",
            "remote": False,
            "contact_name": "",
            "contact_email": "",
            "deadline": None,
            "status": "saved",
            "applied_date": None,
            "created_at": None,
            "notes": [],
            "offer": None,
        }

        for event in events:
            payload = event["payload"]
            timestamp = event["timestamp"]

            if event["event_type"] == APPLICATION_CREATED:
                state.update({
                    "company": payload.get("company", ""),
                    "role": payload.get("role", ""),
                    "url": payload.get("url", ""),
                    "salary_min": payload.get("salary_min"),
                    "salary_max": payload.get("salary_max"),
                    "location": payload.get("location", ""),
                    "remote": payload.get("remote", False),
                    "contact_name": payload.get("contact_name", ""),
                    "contact_email": payload.get("contact_email", ""),
                    "deadline": payload.get("deadline"),
                    "status": payload.get("status", "saved"),
                    "created_at": timestamp,
                })

            elif event["event_type"] == APPLICATION_UPDATED:
                for key in ["company", "role", "url", "salary_min", "salary_max",
                           "location", "remote", "contact_name", "contact_email", "deadline"]:
                    if key in payload:
                        state[key] = payload[key]

            elif event["event_type"] == APPLICATION_STATUS_CHANGED:
                state["status"] = payload.get("status", state["status"])
                if payload.get("applied_date"):
                    state["applied_date"] = payload["applied_date"]

            elif event["event_type"] == NOTE_ADDED:
                state["notes"].append({
                    "note": payload.get("note", ""),
                    "added_at": payload.get("added_at"),
                })

            elif event["event_type"] == OFFER_RECEIVED:
                state["offer"] = {
                    "salary": payload.get("salary"),
                    "bonus": payload.get("bonus", 0),
                    "equity": payload.get("equity", ""),
                    "start_date": payload.get("start_date"),
                    "deadline": payload.get("deadline"),
                    "benefits": payload.get("benefits", ""),
                }

        return state

    def list_applications(
        self,
        status: Optional[str] = None,
        company: Optional[str] = None,
        limit: int = 100,
    ) -> List[dict]:
        """List applications with optional filters."""
        created_events = self.event_store.query(
            entity_type=self.ENTITY_TYPE,
            event_type=APPLICATION_CREATED,
            limit=1000
        )

        apps = []
        for event in created_events:
            app_id = int(event["entity_id"])
            app = self.get(app_id)
            if app:
                if status and app["status"] != status:
                    continue
                if company and company.lower() not in app["company"].lower():
                    continue
                apps.append(app)

        return apps[:limit]

    def get_active(self) -> List[dict]:
        """Get all active applications (not archived/rejected/withdrawn)."""
        apps = self.list_applications(limit=1000)
        active_statuses = ["saved", "applied", "interviewing", "offered"]
        return [a for a in apps if a["status"] in active_statuses]

    def get_stats(self) -> dict:
        """Get job search statistics."""
        apps = self.list_applications(limit=1000)

        by_status = {}
        for app in apps:
            status = app["status"]
            by_status[status] = by_status.get(status, 0) + 1

        # Count interviews
        i_count = len(self.event_store.query(
            entity_type=self.INTERVIEW_ENTITY, event_type=INTERVIEW_SCHEDULED
        ))

        return {
            "total_applications": len(apps),
            "active": len(self.get_active()),
            "by_status": by_status,
            "total_interviews": i_count,
        }

    def explain(self, app_id: int) -> List[dict]:
        """Get event history for an application."""
        return self.event_store.explain(self.ENTITY_TYPE, app_id)
