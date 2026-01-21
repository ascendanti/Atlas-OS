"""
Atlas Personal OS - Research Tracker (KNOW-003)

Event-sourced research project management:
- Track research projects and topics
- Link to PDFs, notes, and ideas
- Track questions, hypotheses, and findings
- Status workflow: active → paused → completed → archived
- Tag-based organization
"""

from __future__ import annotations
from datetime import datetime, date
from typing import Optional, List
from enum import Enum

from modules.core.database import Database, get_database
from modules.core.event_store import EventStore, get_event_store


# Event Types
PROJECT_CREATED = "PROJECT_CREATED"
PROJECT_UPDATED = "PROJECT_UPDATED"
PROJECT_STATUS_CHANGED = "PROJECT_STATUS_CHANGED"
PROJECT_TAGGED = "PROJECT_TAGGED"
QUESTION_ADDED = "QUESTION_ADDED"
QUESTION_ANSWERED = "QUESTION_ANSWERED"
FINDING_ADDED = "FINDING_ADDED"
RESOURCE_LINKED = "RESOURCE_LINKED"
PROJECT_ARCHIVED = "PROJECT_ARCHIVED"


class ProjectStatus(Enum):
    """Research project statuses."""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class ResourceType(Enum):
    """Types of linked resources."""
    PDF = "pdf"
    NOTE = "note"
    IDEA = "idea"
    URL = "url"
    PUBLICATION = "publication"


class ResearchTracker:
    """
    Event-sourced research project tracker.

    Tracks research projects with questions, findings,
    and links to other knowledge resources.
    """

    ENTITY_TYPE = "research_project"
    QUESTION_ENTITY = "research_question"
    FINDING_ENTITY = "research_finding"

    def __init__(
        self,
        db: Optional[Database] = None,
        event_store: Optional[EventStore] = None
    ):
        self.db = db or get_database()
        self.event_store = event_store or get_event_store()
        self._next_id = self._compute_next_id()

    def _compute_next_id(self) -> int:
        """Compute next project ID from events."""
        events = self.event_store.query(
            entity_type=self.ENTITY_TYPE,
            event_type=PROJECT_CREATED
        )
        if not events:
            return 1
        return max(int(e["entity_id"]) for e in events) + 1

    # ========================================================================
    # PROJECT COMMANDS
    # ========================================================================

    def create(
        self,
        title: str,
        description: str = "",
        hypothesis: str = "",
        tags: Optional[List[str]] = None,
        deadline: Optional[date] = None,
    ) -> int:
        """
        Create a new research project.

        Args:
            title: Project title
            description: Project description
            hypothesis: Main hypothesis or research question
            tags: List of tags
            deadline: Target completion date

        Returns:
            Project ID
        """
        project_id = self._next_id
        self._next_id += 1

        self.event_store.emit(
            event_type=PROJECT_CREATED,
            entity_type=self.ENTITY_TYPE,
            entity_id=project_id,
            payload={
                "title": title,
                "description": description,
                "hypothesis": hypothesis,
                "tags": tags or [],
                "deadline": deadline.isoformat() if deadline else None,
                "status": ProjectStatus.ACTIVE.value,
            }
        )
        return project_id

    def update(
        self,
        project_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        hypothesis: Optional[str] = None,
        deadline: Optional[date] = None,
    ) -> bool:
        """Update project details."""
        project = self.get(project_id)
        if not project:
            return False

        payload = {}
        if title is not None:
            payload["title"] = title
        if description is not None:
            payload["description"] = description
        if hypothesis is not None:
            payload["hypothesis"] = hypothesis
        if deadline is not None:
            payload["deadline"] = deadline.isoformat() if deadline else None

        if payload:
            self.event_store.emit(
                event_type=PROJECT_UPDATED,
                entity_type=self.ENTITY_TYPE,
                entity_id=project_id,
                payload=payload
            )
        return True

    def set_status(self, project_id: int, status: ProjectStatus) -> bool:
        """Change project status."""
        project = self.get(project_id)
        if not project:
            return False

        self.event_store.emit(
            event_type=PROJECT_STATUS_CHANGED,
            entity_type=self.ENTITY_TYPE,
            entity_id=project_id,
            payload={"status": status.value, "previous_status": project["status"]}
        )
        return True

    def add_tags(self, project_id: int, tags: List[str]) -> bool:
        """Add tags to a project."""
        project = self.get(project_id)
        if not project:
            return False

        self.event_store.emit(
            event_type=PROJECT_TAGGED,
            entity_type=self.ENTITY_TYPE,
            entity_id=project_id,
            payload={"tags": tags, "action": "add"}
        )
        return True

    def archive(self, project_id: int) -> bool:
        """Archive a project."""
        return self.set_status(project_id, ProjectStatus.ARCHIVED)

    # ========================================================================
    # QUESTIONS & FINDINGS
    # ========================================================================

    def add_question(
        self,
        project_id: int,
        question: str,
        context: str = "",
    ) -> Optional[int]:
        """Add a research question to a project."""
        project = self.get(project_id)
        if not project:
            return None

        # Generate question ID
        q_events = self.event_store.query(
            entity_type=self.QUESTION_ENTITY,
            event_type=QUESTION_ADDED
        )
        q_id = max((int(e["entity_id"]) for e in q_events), default=0) + 1

        self.event_store.emit(
            event_type=QUESTION_ADDED,
            entity_type=self.QUESTION_ENTITY,
            entity_id=q_id,
            payload={
                "project_id": project_id,
                "question": question,
                "context": context,
                "answered": False,
            }
        )
        return q_id

    def answer_question(
        self,
        question_id: int,
        answer: str,
        evidence: str = "",
    ) -> bool:
        """Record an answer to a research question."""
        q = self.get_question(question_id)
        if not q:
            return False

        self.event_store.emit(
            event_type=QUESTION_ANSWERED,
            entity_type=self.QUESTION_ENTITY,
            entity_id=question_id,
            payload={
                "answer": answer,
                "evidence": evidence,
                "answered_at": datetime.now().isoformat(),
            }
        )
        return True

    def add_finding(
        self,
        project_id: int,
        finding: str,
        significance: str = "",
        evidence: str = "",
    ) -> Optional[int]:
        """Record a research finding."""
        project = self.get(project_id)
        if not project:
            return None

        # Generate finding ID
        f_events = self.event_store.query(
            entity_type=self.FINDING_ENTITY,
            event_type=FINDING_ADDED
        )
        f_id = max((int(e["entity_id"]) for e in f_events), default=0) + 1

        self.event_store.emit(
            event_type=FINDING_ADDED,
            entity_type=self.FINDING_ENTITY,
            entity_id=f_id,
            payload={
                "project_id": project_id,
                "finding": finding,
                "significance": significance,
                "evidence": evidence,
            }
        )
        return f_id

    # ========================================================================
    # RESOURCE LINKING
    # ========================================================================

    def link_resource(
        self,
        project_id: int,
        resource_type: ResourceType,
        resource_id: int,
        notes: str = "",
    ) -> bool:
        """Link a resource (PDF, note, idea) to a project."""
        project = self.get(project_id)
        if not project:
            return False

        self.event_store.emit(
            event_type=RESOURCE_LINKED,
            entity_type=self.ENTITY_TYPE,
            entity_id=project_id,
            payload={
                "resource_type": resource_type.value,
                "resource_id": resource_id,
                "notes": notes,
            }
        )
        return True

    # ========================================================================
    # PROJECTIONS
    # ========================================================================

    def get(self, project_id: int) -> Optional[dict]:
        """Get project state by projecting from events."""
        events = self.event_store.explain(self.ENTITY_TYPE, project_id)
        if not events:
            return None

        return self._project(project_id, events)

    def _project(self, project_id: int, events: list[dict]) -> dict:
        """Project state from events."""
        state = {
            "id": project_id,
            "title": "",
            "description": "",
            "hypothesis": "",
            "tags": [],
            "deadline": None,
            "status": "active",
            "created_at": None,
            "linked_resources": [],
        }

        for event in events:
            payload = event["payload"]
            timestamp = event["timestamp"]

            if event["event_type"] == PROJECT_CREATED:
                state["title"] = payload.get("title", "")
                state["description"] = payload.get("description", "")
                state["hypothesis"] = payload.get("hypothesis", "")
                state["tags"] = payload.get("tags", [])
                state["deadline"] = payload.get("deadline")
                state["status"] = payload.get("status", "active")
                state["created_at"] = timestamp

            elif event["event_type"] == PROJECT_UPDATED:
                for key in ["title", "description", "hypothesis", "deadline"]:
                    if key in payload:
                        state[key] = payload[key]

            elif event["event_type"] == PROJECT_STATUS_CHANGED:
                state["status"] = payload.get("status", state["status"])

            elif event["event_type"] == PROJECT_TAGGED:
                if payload.get("action") == "add":
                    for tag in payload.get("tags", []):
                        if tag not in state["tags"]:
                            state["tags"].append(tag)

            elif event["event_type"] == RESOURCE_LINKED:
                state["linked_resources"].append({
                    "type": payload.get("resource_type"),
                    "id": payload.get("resource_id"),
                    "notes": payload.get("notes", ""),
                })

        return state

    def get_question(self, question_id: int) -> Optional[dict]:
        """Get question state."""
        events = self.event_store.explain(self.QUESTION_ENTITY, question_id)
        if not events:
            return None

        state = {
            "id": question_id,
            "project_id": None,
            "question": "",
            "context": "",
            "answered": False,
            "answer": None,
            "evidence": None,
        }

        for event in events:
            payload = event["payload"]
            if event["event_type"] == QUESTION_ADDED:
                state["project_id"] = payload.get("project_id")
                state["question"] = payload.get("question", "")
                state["context"] = payload.get("context", "")
            elif event["event_type"] == QUESTION_ANSWERED:
                state["answered"] = True
                state["answer"] = payload.get("answer")
                state["evidence"] = payload.get("evidence")

        return state

    def get_questions(self, project_id: int) -> List[dict]:
        """Get all questions for a project."""
        q_events = self.event_store.query(
            entity_type=self.QUESTION_ENTITY,
            event_type=QUESTION_ADDED
        )

        questions = []
        for event in q_events:
            if event["payload"].get("project_id") == project_id:
                q_id = int(event["entity_id"])
                q = self.get_question(q_id)
                if q:
                    questions.append(q)

        return questions

    def get_findings(self, project_id: int) -> List[dict]:
        """Get all findings for a project."""
        f_events = self.event_store.query(
            entity_type=self.FINDING_ENTITY,
            event_type=FINDING_ADDED
        )

        findings = []
        for event in f_events:
            if event["payload"].get("project_id") == project_id:
                findings.append({
                    "id": int(event["entity_id"]),
                    "finding": event["payload"].get("finding", ""),
                    "significance": event["payload"].get("significance", ""),
                    "evidence": event["payload"].get("evidence", ""),
                    "timestamp": event["timestamp"],
                })

        return findings

    def list_projects(
        self,
        status: Optional[str] = None,
        tag: Optional[str] = None,
        limit: int = 100,
    ) -> List[dict]:
        """List projects with optional filters."""
        created_events = self.event_store.query(
            entity_type=self.ENTITY_TYPE,
            event_type=PROJECT_CREATED,
            limit=1000
        )

        projects = []
        for event in created_events:
            project_id = int(event["entity_id"])
            project = self.get(project_id)
            if project:
                if status and project["status"] != status:
                    continue
                if tag and tag not in project["tags"]:
                    continue
                projects.append(project)

        return projects[:limit]

    def search(self, query: str, limit: int = 50) -> List[dict]:
        """Search projects by title, description, or hypothesis."""
        query_lower = query.lower()
        projects = self.list_projects(limit=1000)

        results = []
        for p in projects:
            if (query_lower in p["title"].lower() or
                query_lower in p["description"].lower() or
                query_lower in p["hypothesis"].lower()):
                results.append(p)

        return results[:limit]

    def get_stats(self) -> dict:
        """Get research statistics."""
        projects = self.list_projects(limit=1000)
        active = len([p for p in projects if p["status"] == "active"])
        completed = len([p for p in projects if p["status"] == "completed"])

        # Count questions and findings
        q_count = len(self.event_store.query(
            entity_type=self.QUESTION_ENTITY, event_type=QUESTION_ADDED
        ))
        f_count = len(self.event_store.query(
            entity_type=self.FINDING_ENTITY, event_type=FINDING_ADDED
        ))

        return {
            "total_projects": len(projects),
            "active": active,
            "completed": completed,
            "total_questions": q_count,
            "total_findings": f_count,
        }

    def explain(self, project_id: int) -> List[dict]:
        """Get event history for a project."""
        return self.event_store.explain(self.ENTITY_TYPE, project_id)
