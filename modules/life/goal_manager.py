"""
Atlas Personal OS - Goal Manager (LIFE-003)

Event-sourced goal tracking implementing the Event Spine invariant:
COMMAND → EVENT → PROJECTION

Goals are projections computed entirely from events.
No direct table mutations - events are the single source of truth.
"""

from datetime import datetime, date
from typing import Optional, Any
from modules.core.database import Database, get_database
from modules.core.event_store import EventStore, get_event_store


# Event Types
GOAL_DEFINED = "GOAL_DEFINED"
GOAL_TARGET_SET = "GOAL_TARGET_SET"
GOAL_UPDATED = "GOAL_UPDATED"


class GoalManager:
    """
    Event-sourced goal manager.

    All state is derived from events - no direct database mutations.
    """

    ENTITY_TYPE = "goal"

    def __init__(
        self,
        db: Optional[Database] = None,
        event_store: Optional[EventStore] = None
    ):
        """Initialize goal manager with event store."""
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

    def define(self, title: str, description: str = "") -> int:
        """
        Define a new goal.

        Command: Creates a goal definition.
        Event: GOAL_DEFINED with title, description.

        Args:
            title: Goal title
            description: Goal description

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
            }
        )
        return goal_id

    def set_target(
        self,
        goal_id: int,
        target_date: date,
        target_value: int = 100
    ) -> bool:
        """
        Set target date and value for a goal.

        Command: Sets a goal's target.
        Event: GOAL_TARGET_SET with target_date, target_value.

        Args:
            goal_id: Goal ID
            target_date: Target completion date
            target_value: Target value (default 100 for percentage-based)

        Returns:
            True if goal exists and target was set
        """
        goal = self.get(goal_id)
        if not goal:
            return False

        self.event_store.emit(
            event_type=GOAL_TARGET_SET,
            entity_type=self.ENTITY_TYPE,
            entity_id=goal_id,
            payload={
                "target_date": target_date.isoformat(),
                "target_value": target_value,
            }
        )
        return True

    def update_progress(self, goal_id: int, current_value: int, note: str = "") -> bool:
        """
        Update progress on a goal.

        Command: Records progress.
        Event: GOAL_UPDATED with current_value, note.

        Args:
            goal_id: Goal ID
            current_value: Current progress value
            note: Optional progress note

        Returns:
            True if goal exists and was updated
        """
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

    def get(self, goal_id: int) -> Optional[dict]:
        """
        Get goal state by projecting from events.

        Projection: Computes current state from event history.

        Args:
            goal_id: Goal ID

        Returns:
            Goal state dict or None if not found
        """
        events = self.event_store.explain(self.ENTITY_TYPE, goal_id)
        if not events:
            return None

        return self._project_goal(goal_id, events)

    def _project_goal(self, goal_id: int, events: list[dict]) -> dict:
        """
        Project goal state from events.

        Applies events in order to compute current state.
        """
        state = {
            "id": goal_id,
            "title": "",
            "description": "",
            "target_date": None,
            "target_value": 100,
            "current_value": 0,
            "created_at": None,
            "last_updated": None,
        }

        for event in events:
            payload = event["payload"]
            timestamp = event["timestamp"]

            if event["event_type"] == GOAL_DEFINED:
                state["title"] = payload.get("title", "")
                state["description"] = payload.get("description", "")
                state["created_at"] = timestamp

            elif event["event_type"] == GOAL_TARGET_SET:
                state["target_date"] = payload.get("target_date")
                state["target_value"] = payload.get("target_value", 100)

            elif event["event_type"] == GOAL_UPDATED:
                state["current_value"] = payload.get("current_value", 0)
                state["last_updated"] = timestamp

        return state

    def list_goals(self, limit: int = 100) -> list[dict]:
        """
        List all goals by projecting from events.

        Projection: Finds all GOAL_DEFINED events and projects each.

        Args:
            limit: Maximum goals to return

        Returns:
            List of goal state dicts
        """
        # Get all goal definitions
        defined_events = self.event_store.query(
            entity_type=self.ENTITY_TYPE,
            event_type=GOAL_DEFINED,
            limit=limit
        )

        goals = []
        for event in defined_events:
            goal_id = int(event["entity_id"])
            goal = self.get(goal_id)
            if goal:
                goals.append(goal)

        return goals

    def progress(self, goal_id: int) -> Optional[dict]:
        """
        Get progress summary for a goal.

        Projection: Computes progress percentage and status.

        Args:
            goal_id: Goal ID

        Returns:
            Progress dict with percentage, status, days_remaining
        """
        goal = self.get(goal_id)
        if not goal:
            return None

        target_value = goal["target_value"]
        current_value = goal["current_value"]
        percentage = (current_value / target_value * 100) if target_value > 0 else 0

        # Compute days remaining
        days_remaining = None
        if goal["target_date"]:
            target = date.fromisoformat(goal["target_date"])
            days_remaining = (target - date.today()).days

        # Determine status
        if percentage >= 100:
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
            "current_value": current_value,
            "target_value": target_value,
            "percentage": round(percentage, 1),
            "target_date": goal["target_date"],
            "days_remaining": days_remaining,
            "status": status,
        }

    def explain(self, goal_id: int) -> list[dict]:
        """
        Get event history for a goal (audit trail).

        Returns chronological list of all events for the goal.

        Args:
            goal_id: Goal ID

        Returns:
            List of events in chronological order
        """
        return self.event_store.explain(self.ENTITY_TYPE, goal_id)
