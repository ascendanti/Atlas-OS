"""
Atlas Personal OS - Enhanced Goal Manager (LIFE-003 v2)

Event-sourced goal tracking with OKR support:
- Areas of life (Health, Career, Finance, Relationships, etc.)
- Key Results (OKR-style metrics)
- Milestones (intermediate checkpoints)
- Goal hierarchy (parent/child goals)
- Progress history tracking

Event Spine: COMMAND → EVENT → PROJECTION
Goals are projections computed entirely from events.
"""

from __future__ import annotations
from datetime import datetime, date, timedelta
from typing import Optional, List
from enum import Enum
import json

from modules.core.database import Database, get_database
from modules.core.event_store import EventStore, get_event_store


# Event Types
GOAL_DEFINED = "GOAL_DEFINED"
GOAL_TARGET_SET = "GOAL_TARGET_SET"
GOAL_UPDATED = "GOAL_UPDATED"
GOAL_AREA_SET = "GOAL_AREA_SET"
GOAL_PARENT_SET = "GOAL_PARENT_SET"
GOAL_ARCHIVED = "GOAL_ARCHIVED"
KEY_RESULT_ADDED = "KEY_RESULT_ADDED"
KEY_RESULT_UPDATED = "KEY_RESULT_UPDATED"
MILESTONE_ADDED = "MILESTONE_ADDED"
MILESTONE_COMPLETED = "MILESTONE_COMPLETED"
PROGRESS_LOGGED = "PROGRESS_LOGGED"


class AreaOfLife(Enum):
    """Categories for life areas."""
    HEALTH = "health"
    CAREER = "career"
    FINANCE = "finance"
    RELATIONSHIPS = "relationships"
    PERSONAL_GROWTH = "personal_growth"
    CREATIVITY = "creativity"
    SPIRITUALITY = "spirituality"
    FUN = "fun"
    ENVIRONMENT = "environment"
    OTHER = "other"


class GoalStatus(Enum):
    """Goal statuses."""
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    ON_HOLD = "on_hold"


class GoalManager:
    """
    Enhanced event-sourced goal manager with OKR support.

    Features:
    - Areas of life categorization
    - Key Results (OKR-style metrics)
    - Milestones with completion tracking
    - Goal hierarchy (parent/child)
    - Rich progress history
    """

    ENTITY_TYPE = "goal"
    KR_ENTITY_TYPE = "key_result"
    MILESTONE_ENTITY_TYPE = "milestone"

    def __init__(
        self,
        db: Optional[Database] = None,
        event_store: Optional[EventStore] = None
    ):
        self.db = db or get_database()
        self.event_store = event_store or get_event_store()
        self._next_id = self._compute_next_id()

    def _compute_next_id(self) -> int:
        """Compute next goal ID from existing events."""
        events = self.event_store.query(
            entity_type=self.ENTITY_TYPE,
            event_type=GOAL_DEFINED
        )
        if not events:
            return 1
        max_id = max(int(e["entity_id"]) for e in events)
        return max_id + 1

    # ========================================================================
    # GOAL COMMANDS
    # ========================================================================

    def define(
        self,
        title: str,
        description: str = "",
        area: AreaOfLife = AreaOfLife.OTHER,
        parent_id: Optional[int] = None,
        target_date: Optional[date] = None,
        target_value: int = 100,
    ) -> int:
        """
        Define a new goal (Objective in OKR terms).

        Args:
            title: Goal title
            description: Goal description
            area: Area of life category
            parent_id: Parent goal ID (for hierarchy)
            target_date: Target completion date
            target_value: Target value (default 100 for percentage)

        Returns:
            Goal ID
        """
        goal_id = self._next_id
        self._next_id += 1

        self.event_store.emit(
            event_type=GOAL_DEFINED,
            entity_type=self.ENTITY_TYPE,
            entity_id=goal_id,
            payload={
                "title": title,
                "description": description,
                "area": area.value if isinstance(area, AreaOfLife) else area,
                "parent_id": parent_id,
                "target_date": target_date.isoformat() if target_date else None,
                "target_value": target_value,
            }
        )
        return goal_id

    def set_target(
        self,
        goal_id: int,
        target_date: date,
        target_value: int = 100
    ) -> bool:
        """Set target date and value for a goal."""
        goal = self.get(goal_id)
        if not goal:
            return False

        self.event_store.emit(
            event_type=GOAL_TARGET_SET,
            entity_type=self.ENTITY_TYPE,
            entity_id=goal_id,
            payload={
                "target_date": target_date.isoformat() if isinstance(target_date, date) else target_date,
                "target_value": target_value,
            }
        )
        return True

    def update_progress(self, goal_id: int, current_value: int, note: str = "") -> bool:
        """Update progress on a goal (legacy method - kept for compatibility)."""
        goal = self.get(goal_id)
        if not goal:
            return False

        self.event_store.emit(
            event_type=GOAL_UPDATED,
            entity_type=self.ENTITY_TYPE,
            entity_id=goal_id,
            payload={
                "current_value": current_value,
                "note": note,
            }
        )
        return True

    def set_area(self, goal_id: int, area: AreaOfLife) -> bool:
        """Set the area of life for a goal."""
        goal = self.get(goal_id)
        if not goal:
            return False

        self.event_store.emit(
            event_type=GOAL_AREA_SET,
            entity_type=self.ENTITY_TYPE,
            entity_id=goal_id,
            payload={"area": area.value}
        )
        return True

    def set_parent(self, goal_id: int, parent_id: Optional[int]) -> bool:
        """Set parent goal (for hierarchy)."""
        goal = self.get(goal_id)
        if not goal:
            return False
        if parent_id and not self.get(parent_id):
            return False

        self.event_store.emit(
            event_type=GOAL_PARENT_SET,
            entity_type=self.ENTITY_TYPE,
            entity_id=goal_id,
            payload={"parent_id": parent_id}
        )
        return True

    def archive(self, goal_id: int) -> bool:
        """Archive a goal."""
        goal = self.get(goal_id)
        if not goal or goal.get("status") == "archived":
            return False

        self.event_store.emit(
            event_type=GOAL_ARCHIVED,
            entity_type=self.ENTITY_TYPE,
            entity_id=goal_id,
            payload={"archived_at": datetime.now().isoformat()}
        )
        return True

    # ========================================================================
    # KEY RESULTS (OKR)
    # ========================================================================

    def add_key_result(
        self,
        goal_id: int,
        title: str,
        target_value: int = 100,
        unit: str = "%",
        description: str = "",
    ) -> Optional[int]:
        """
        Add a Key Result to an Objective (goal).

        Args:
            goal_id: Parent goal/objective ID
            title: Key result title (measurable metric)
            target_value: Target value to achieve
            unit: Unit of measurement (%, count, hours, etc.)
            description: Additional details

        Returns:
            Key Result ID or None if goal doesn't exist
        """
        goal = self.get(goal_id)
        if not goal:
            return None

        # Generate KR ID
        kr_events = self.event_store.query(
            entity_type=self.KR_ENTITY_TYPE,
            event_type=KEY_RESULT_ADDED
        )
        kr_id = max((int(e["entity_id"]) for e in kr_events), default=0) + 1

        self.event_store.emit(
            event_type=KEY_RESULT_ADDED,
            entity_type=self.KR_ENTITY_TYPE,
            entity_id=kr_id,
            payload={
                "goal_id": goal_id,
                "title": title,
                "target_value": target_value,
                "current_value": 0,
                "unit": unit,
                "description": description,
            }
        )
        return kr_id

    def update_key_result(
        self,
        kr_id: int,
        current_value: int,
        note: str = ""
    ) -> bool:
        """Update progress on a Key Result."""
        kr = self.get_key_result(kr_id)
        if not kr:
            return False

        self.event_store.emit(
            event_type=KEY_RESULT_UPDATED,
            entity_type=self.KR_ENTITY_TYPE,
            entity_id=kr_id,
            payload={
                "current_value": current_value,
                "note": note,
            }
        )
        return True

    def get_key_result(self, kr_id: int) -> Optional[dict]:
        """Get a Key Result by projecting from events."""
        events = self.event_store.explain(self.KR_ENTITY_TYPE, kr_id)
        if not events:
            return None

        state = {
            "id": kr_id,
            "goal_id": None,
            "title": "",
            "target_value": 100,
            "current_value": 0,
            "unit": "%",
            "description": "",
        }

        for event in events:
            payload = event["payload"]
            if event["event_type"] == KEY_RESULT_ADDED:
                state.update({
                    "goal_id": payload.get("goal_id"),
                    "title": payload.get("title", ""),
                    "target_value": payload.get("target_value", 100),
                    "unit": payload.get("unit", "%"),
                    "description": payload.get("description", ""),
                })
            elif event["event_type"] == KEY_RESULT_UPDATED:
                state["current_value"] = payload.get("current_value", state["current_value"])

        return state

    def get_key_results(self, goal_id: int) -> List[dict]:
        """Get all Key Results for a goal."""
        kr_events = self.event_store.query(
            entity_type=self.KR_ENTITY_TYPE,
            event_type=KEY_RESULT_ADDED
        )

        results = []
        for event in kr_events:
            if event["payload"].get("goal_id") == goal_id:
                kr_id = int(event["entity_id"])
                kr = self.get_key_result(kr_id)
                if kr:
                    # Add percentage
                    kr["percentage"] = round(
                        kr["current_value"] / kr["target_value"] * 100, 1
                    ) if kr["target_value"] > 0 else 0
                    results.append(kr)

        return results

    # ========================================================================
    # MILESTONES
    # ========================================================================

    def add_milestone(
        self,
        goal_id: int,
        title: str,
        target_date: Optional[date] = None,
        description: str = "",
    ) -> Optional[int]:
        """
        Add a milestone to a goal.

        Args:
            goal_id: Goal ID
            title: Milestone title
            target_date: Target completion date
            description: Details

        Returns:
            Milestone ID or None if goal doesn't exist
        """
        goal = self.get(goal_id)
        if not goal:
            return None

        # Generate milestone ID
        ms_events = self.event_store.query(
            entity_type=self.MILESTONE_ENTITY_TYPE,
            event_type=MILESTONE_ADDED
        )
        ms_id = max((int(e["entity_id"]) for e in ms_events), default=0) + 1

        self.event_store.emit(
            event_type=MILESTONE_ADDED,
            entity_type=self.MILESTONE_ENTITY_TYPE,
            entity_id=ms_id,
            payload={
                "goal_id": goal_id,
                "title": title,
                "target_date": target_date.isoformat() if target_date else None,
                "description": description,
                "completed": False,
            }
        )
        return ms_id

    def complete_milestone(self, ms_id: int) -> bool:
        """Mark a milestone as completed."""
        ms = self.get_milestone(ms_id)
        if not ms or ms.get("completed"):
            return False

        self.event_store.emit(
            event_type=MILESTONE_COMPLETED,
            entity_type=self.MILESTONE_ENTITY_TYPE,
            entity_id=ms_id,
            payload={"completed_at": datetime.now().isoformat()}
        )
        return True

    def get_milestone(self, ms_id: int) -> Optional[dict]:
        """Get a milestone by projecting from events."""
        events = self.event_store.explain(self.MILESTONE_ENTITY_TYPE, ms_id)
        if not events:
            return None

        state = {
            "id": ms_id,
            "goal_id": None,
            "title": "",
            "target_date": None,
            "description": "",
            "completed": False,
            "completed_at": None,
        }

        for event in events:
            payload = event["payload"]
            if event["event_type"] == MILESTONE_ADDED:
                state.update({
                    "goal_id": payload.get("goal_id"),
                    "title": payload.get("title", ""),
                    "target_date": payload.get("target_date"),
                    "description": payload.get("description", ""),
                })
            elif event["event_type"] == MILESTONE_COMPLETED:
                state["completed"] = True
                state["completed_at"] = payload.get("completed_at")

        return state

    def get_milestones(self, goal_id: int) -> List[dict]:
        """Get all milestones for a goal."""
        ms_events = self.event_store.query(
            entity_type=self.MILESTONE_ENTITY_TYPE,
            event_type=MILESTONE_ADDED
        )

        results = []
        for event in ms_events:
            if event["payload"].get("goal_id") == goal_id:
                ms_id = int(event["entity_id"])
                ms = self.get_milestone(ms_id)
                if ms:
                    results.append(ms)

        # Sort by target_date (None dates at end)
        return sorted(results, key=lambda x: (x["target_date"] is None, x["target_date"] or ""))

    # ========================================================================
    # PROGRESS HISTORY
    # ========================================================================

    def log_progress(
        self,
        goal_id: int,
        value: int,
        note: str = "",
        reflection: str = "",
    ) -> bool:
        """
        Log a progress entry with optional reflection.

        Args:
            goal_id: Goal ID
            value: Progress value at this point
            note: Brief note
            reflection: Longer reflection text

        Returns:
            True if logged successfully
        """
        goal = self.get(goal_id)
        if not goal:
            return False

        self.event_store.emit(
            event_type=PROGRESS_LOGGED,
            entity_type=self.ENTITY_TYPE,
            entity_id=goal_id,
            payload={
                "value": value,
                "note": note,
                "reflection": reflection,
                "logged_at": datetime.now().isoformat(),
            }
        )
        return True

    def get_progress_history(self, goal_id: int) -> List[dict]:
        """Get progress history for a goal."""
        events = self.event_store.explain(self.ENTITY_TYPE, goal_id)
        history = []

        for event in events:
            if event["event_type"] in [GOAL_UPDATED, PROGRESS_LOGGED]:
                payload = event["payload"]
                entry = {
                    "timestamp": event["timestamp"],
                    "value": payload.get("value") or payload.get("current_value", 0),
                    "note": payload.get("note", ""),
                    "reflection": payload.get("reflection", ""),
                }
                history.append(entry)

        return history

    # ========================================================================
    # PROJECTIONS
    # ========================================================================

    def get(self, goal_id: int) -> Optional[dict]:
        """Get goal state by projecting from events."""
        events = self.event_store.explain(self.ENTITY_TYPE, goal_id)
        if not events:
            return None

        return self._project_goal(goal_id, events)

    def _project_goal(self, goal_id: int, events: list[dict]) -> dict:
        """Project goal state from events."""
        state = {
            "id": goal_id,
            "title": "",
            "description": "",
            "area": "other",
            "parent_id": None,
            "target_date": None,
            "target_value": 100,
            "current_value": 0,
            "status": "active",
            "created_at": None,
            "last_updated": None,
            "archived_at": None,
        }

        for event in events:
            payload = event["payload"]
            timestamp = event["timestamp"]

            if event["event_type"] == GOAL_DEFINED:
                state["title"] = payload.get("title", "")
                state["description"] = payload.get("description", "")
                state["area"] = payload.get("area", "other")
                state["parent_id"] = payload.get("parent_id")
                state["target_date"] = payload.get("target_date")
                state["target_value"] = payload.get("target_value", 100)
                state["created_at"] = timestamp

            elif event["event_type"] == GOAL_TARGET_SET:
                state["target_date"] = payload.get("target_date")
                state["target_value"] = payload.get("target_value", 100)

            elif event["event_type"] == GOAL_UPDATED:
                state["current_value"] = payload.get("current_value", 0)
                state["last_updated"] = timestamp

            elif event["event_type"] == GOAL_AREA_SET:
                state["area"] = payload.get("area", "other")

            elif event["event_type"] == GOAL_PARENT_SET:
                state["parent_id"] = payload.get("parent_id")

            elif event["event_type"] == GOAL_ARCHIVED:
                state["status"] = "archived"
                state["archived_at"] = payload.get("archived_at")

            elif event["event_type"] == PROGRESS_LOGGED:
                state["current_value"] = payload.get("value", state["current_value"])
                state["last_updated"] = timestamp

        # Compute status if not archived
        if state["status"] != "archived":
            if state["current_value"] >= state["target_value"]:
                state["status"] = "completed"

        return state

    def list_goals(
        self,
        limit: int = 100,
        area: Optional[AreaOfLife] = None,
        status: Optional[str] = None,
        parent_id: Optional[int] = None,
        include_archived: bool = False,
    ) -> list[dict]:
        """
        List goals with filters.

        Args:
            limit: Maximum goals to return
            area: Filter by area of life
            status: Filter by status
            parent_id: Filter by parent goal (None for top-level)
            include_archived: Include archived goals

        Returns:
            List of goal state dicts
        """
        defined_events = self.event_store.query(
            entity_type=self.ENTITY_TYPE,
            event_type=GOAL_DEFINED,
            limit=1000
        )

        goals = []
        for event in defined_events:
            goal_id = int(event["entity_id"])
            goal = self.get(goal_id)
            if goal:
                # Apply filters
                if area and goal["area"] != area.value:
                    continue
                if status and goal["status"] != status:
                    continue
                if not include_archived and goal["status"] == "archived":
                    continue
                if parent_id is not None and goal["parent_id"] != parent_id:
                    continue

                goals.append(goal)

        return goals[:limit]

    def get_children(self, goal_id: int) -> List[dict]:
        """Get child goals of a parent goal."""
        return self.list_goals(parent_id=goal_id, limit=1000)

    def get_by_area(self, area: AreaOfLife) -> List[dict]:
        """Get all goals in an area of life."""
        return self.list_goals(area=area, limit=1000)

    def get_top_level_goals(self) -> List[dict]:
        """Get goals that have no parent (top-level objectives)."""
        all_goals = self.list_goals(limit=1000)
        return [g for g in all_goals if g["parent_id"] is None]

    # ========================================================================
    # PROGRESS & STATISTICS
    # ========================================================================

    def progress(self, goal_id: int) -> Optional[dict]:
        """Get progress summary for a goal including Key Results."""
        goal = self.get(goal_id)
        if not goal:
            return None

        target_value = goal["target_value"]
        current_value = goal["current_value"]
        percentage = (current_value / target_value * 100) if target_value > 0 else 0

        # Get Key Results and their average progress
        key_results = self.get_key_results(goal_id)
        kr_avg = 0
        if key_results:
            kr_avg = sum(kr["percentage"] for kr in key_results) / len(key_results)
            # Use KR average if we have KRs and no direct progress
            if current_value == 0 and kr_avg > 0:
                percentage = kr_avg

        # Get milestones
        milestones = self.get_milestones(goal_id)
        ms_completed = len([m for m in milestones if m["completed"]])
        ms_total = len(milestones)

        # Compute days remaining
        days_remaining = None
        if goal["target_date"]:
            target = date.fromisoformat(goal["target_date"])
            days_remaining = (target - date.today()).days

        # Determine status
        if goal["status"] == "archived":
            status = "archived"
        elif percentage >= 100:
            status = "completed"
        elif days_remaining is not None and days_remaining < 0:
            status = "overdue"
        elif days_remaining is not None and days_remaining <= 7:
            status = "urgent"
        else:
            status = "active"

        return {
            "goal_id": goal_id,
            "title": goal["title"],
            "area": goal["area"],
            "current_value": current_value,
            "target_value": target_value,
            "percentage": round(percentage, 1),
            "target_date": goal["target_date"],
            "days_remaining": days_remaining,
            "status": status,
            "key_results": {
                "count": len(key_results),
                "average_progress": round(kr_avg, 1),
            },
            "milestones": {
                "completed": ms_completed,
                "total": ms_total,
            },
        }

    def get_stats(self) -> dict:
        """Get overall goal statistics."""
        goals = self.list_goals(limit=1000, include_archived=True)
        active = [g for g in goals if g["status"] == "active"]
        completed = [g for g in goals if g["status"] == "completed"]
        archived = [g for g in goals if g["status"] == "archived"]

        # By area
        by_area = {}
        for area in AreaOfLife:
            area_goals = [g for g in goals if g["area"] == area.value]
            if area_goals:
                by_area[area.value] = {
                    "total": len(area_goals),
                    "active": len([g for g in area_goals if g["status"] == "active"]),
                    "completed": len([g for g in area_goals if g["status"] == "completed"]),
                }

        return {
            "total": len(goals),
            "active": len(active),
            "completed": len(completed),
            "archived": len(archived),
            "completion_rate": round(len(completed) / len(goals) * 100, 1) if goals else 0,
            "by_area": by_area,
        }

    def explain(self, goal_id: int) -> list[dict]:
        """Get event history for a goal (audit trail)."""
        return self.event_store.explain(self.ENTITY_TYPE, goal_id)
