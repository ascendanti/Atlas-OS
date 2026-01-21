"""
Atlas Personal OS - Weekly Review System

GTD-inspired weekly review module that generates comprehensive
review reports covering tasks, goals, habits, and provides
reflection prompts.

Features:
- Weekly/monthly review generation
- Task completion analysis
- Goal progress tracking
- Habit streak summaries
- Review history with reflections
- Upcoming week planning
"""

from __future__ import annotations
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from enum import Enum

from modules.core.database import Database, get_database
from modules.core.event_store import EventStore, get_event_store


class ReviewType(Enum):
    """Review period types."""
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"


class WeeklyReview:
    """
    Weekly review system for GTD-style reflection and planning.

    Aggregates data from tasks, goals, habits, and events
    to provide a comprehensive review of the period.
    """

    TABLE_NAME = "reviews"
    SCHEMA = """
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        review_type TEXT DEFAULT 'weekly',
        period_start DATE NOT NULL,
        period_end DATE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP,
        -- Review content (JSON)
        summary TEXT DEFAULT '{}',
        reflections TEXT DEFAULT '{}',
        next_week_focus TEXT DEFAULT '[]',
        -- Status
        status TEXT DEFAULT 'draft'
    """

    def __init__(
        self,
        db: Optional[Database] = None,
        event_store: Optional[EventStore] = None
    ):
        self.db = db or get_database()
        self.event_store = event_store or get_event_store()
        self._ensure_table()

    def _ensure_table(self) -> None:
        self.db.create_table(self.TABLE_NAME, self.SCHEMA)

    # ========================================================================
    # REVIEW GENERATION
    # ========================================================================

    def generate_review(
        self,
        review_type: ReviewType = ReviewType.WEEKLY,
        period_end: Optional[date] = None,
    ) -> dict:
        """
        Generate a review for the specified period.

        Args:
            review_type: Type of review (weekly, monthly, quarterly)
            period_end: End date of period (defaults to today)

        Returns:
            Review data dict with all metrics and summaries
        """
        end_date = period_end or date.today()

        # Calculate period start based on review type
        if review_type == ReviewType.WEEKLY:
            # Start from Monday of the week
            start_date = end_date - timedelta(days=end_date.weekday())
            if start_date == end_date:
                start_date = end_date - timedelta(days=7)
        elif review_type == ReviewType.MONTHLY:
            start_date = end_date.replace(day=1)
        else:  # QUARTERLY
            quarter_month = ((end_date.month - 1) // 3) * 3 + 1
            start_date = end_date.replace(month=quarter_month, day=1)

        # Generate review sections
        review_data = {
            "review_type": review_type.value,
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "generated_at": datetime.now().isoformat(),
            "tasks": self._get_task_summary(start_date, end_date),
            "goals": self._get_goal_summary(start_date, end_date),
            "habits": self._get_habit_summary(start_date, end_date),
            "events": self._get_event_summary(start_date, end_date),
            "upcoming": self._get_upcoming_items(),
            "reflection_prompts": self._get_reflection_prompts(review_type),
        }

        return review_data

    def _get_task_summary(self, start: date, end: date) -> dict:
        """Get task metrics for the period."""
        from modules.life.task_tracker import TaskTracker
        tracker = TaskTracker(db=self.db, event_store=self.event_store)

        # Query events for task completions in period
        events = self.event_store.query(
            entity_type="task",
            event_type="TASK_COMPLETED",
            limit=1000
        )

        completed_in_period = []
        for e in events:
            timestamp = e.get("timestamp", "")
            if timestamp:
                event_date = datetime.fromisoformat(timestamp.replace("Z", "")).date()
                if start <= event_date <= end:
                    completed_in_period.append(e)

        # Get current task stats
        try:
            stats = tracker.get_stats()
        except:
            stats = {"pending": 0, "overdue": 0, "due_today": 0}

        # Get overdue tasks
        try:
            overdue = tracker.get_overdue()
        except:
            overdue = []

        return {
            "completed_count": len(completed_in_period),
            "pending_count": stats.get("pending", 0),
            "overdue_count": len(overdue),
            "overdue_tasks": [{"id": t["id"], "title": t["title"], "due_date": t.get("due_date")}
                            for t in overdue[:5]],
            "completion_rate": stats.get("completion_rate", 0),
        }

    def _get_goal_summary(self, start: date, end: date) -> dict:
        """Get goal metrics for the period."""
        from modules.life.goal_manager import GoalManager
        manager = GoalManager(db=self.db, event_store=self.event_store)

        # Get all goals
        try:
            goals = manager.list_goals(limit=1000)
        except:
            goals = []

        active = [g for g in goals if g.get("status") == "active"]
        completed = [g for g in goals if g.get("status") == "completed"]

        # Goals with progress updates in period
        updated_goals = []
        for goal in goals:
            events = manager.explain(goal["id"])
            for e in events:
                timestamp = e.get("timestamp", "")
                if timestamp:
                    event_date = datetime.fromisoformat(timestamp.replace("Z", "")).date()
                    if start <= event_date <= end and e["event_type"] in ["GOAL_UPDATED", "PROGRESS_LOGGED"]:
                        updated_goals.append(goal)
                        break

        # Calculate average progress of active goals
        avg_progress = 0
        if active:
            total_progress = sum(
                (g.get("current_value", 0) / g.get("target_value", 100)) * 100
                for g in active
            )
            avg_progress = round(total_progress / len(active), 1)

        return {
            "active_count": len(active),
            "completed_count": len(completed),
            "updated_this_period": len(updated_goals),
            "average_progress": avg_progress,
            "goals_needing_attention": [
                {"id": g["id"], "title": g["title"], "progress": g.get("current_value", 0)}
                for g in active if g.get("current_value", 0) < 25
            ][:5],
        }

    def _get_habit_summary(self, start: date, end: date) -> dict:
        """Get habit metrics for the period."""
        from modules.life.habit_tracker import HabitTracker
        tracker = HabitTracker(db=self.db)

        try:
            habits = tracker.list_habits()
            today_status = tracker.get_today_status() or []
        except:
            habits = []
            today_status = {}

        status_map = {h["id"]: h for h in today_status} if today_status else {}

        # Get streaks and completion rates
        habit_data = []
        for h in habits:
            status = status_map.get(h["id"], {})
            try:
                rate = tracker.get_completion_rate(h["id"], days=7)
            except:
                rate = 0

            habit_data.append({
                "id": h["id"],
                "name": h["name"],
                "current_streak": status.get("current_streak", 0),
                "completed_today": status.get("completed_today", False),
                "weekly_rate": round(rate, 1),
            })

        # Sort by streak (highest first)
        habit_data.sort(key=lambda x: x["current_streak"], reverse=True)

        return {
            "total_habits": len(habits),
            "completed_today": len([h for h in habit_data if h["completed_today"]]),
            "average_weekly_rate": round(
                sum(h["weekly_rate"] for h in habit_data) / len(habit_data), 1
            ) if habit_data else 0,
            "top_streaks": habit_data[:3],
            "needs_attention": [h for h in habit_data if h["weekly_rate"] < 50][:3],
        }

    def _get_event_summary(self, start: date, end: date) -> dict:
        """Get system event summary for audit/activity tracking."""
        # Get all events in period
        all_events = self.event_store.query(limit=10000)

        events_in_period = []
        for e in all_events:
            timestamp = e.get("timestamp", "")
            if timestamp:
                try:
                    event_date = datetime.fromisoformat(timestamp.replace("Z", "")).date()
                    if start <= event_date <= end:
                        events_in_period.append(e)
                except:
                    pass

        # Count by type
        by_type = {}
        for e in events_in_period:
            et = e.get("event_type", "unknown")
            by_type[et] = by_type.get(et, 0) + 1

        return {
            "total_events": len(events_in_period),
            "by_type": dict(sorted(by_type.items(), key=lambda x: -x[1])[:10]),
        }

    def _get_upcoming_items(self) -> dict:
        """Get items due in the next week."""
        from modules.life.task_tracker import TaskTracker
        from modules.life.event_reminder import EventReminder

        tracker = TaskTracker(db=self.db, event_store=self.event_store)
        reminder = EventReminder(db=self.db, event_store=self.event_store)

        try:
            upcoming_tasks = tracker.get_upcoming(days=7)
        except:
            upcoming_tasks = []

        try:
            upcoming_reminders = reminder.upcoming(days=7)
        except:
            upcoming_reminders = []

        return {
            "tasks": [{"id": t["id"], "title": t["title"], "due_date": t.get("due_date")}
                     for t in upcoming_tasks[:10]],
            "reminders": [{"id": r["id"], "title": r["title"], "event_date": r.get("event_date")}
                         for r in upcoming_reminders[:10]],
        }

    def _get_reflection_prompts(self, review_type: ReviewType) -> List[str]:
        """Get reflection prompts based on review type."""
        weekly_prompts = [
            "What was your biggest win this week?",
            "What didn't go as planned? What can you learn from it?",
            "What are your top 3 priorities for next week?",
            "Is there anything you've been procrastinating on?",
            "Who helped you this week? Have you thanked them?",
            "What habit or routine served you well this week?",
        ]

        monthly_prompts = [
            "What progress did you make toward your major goals?",
            "What new skills or knowledge did you acquire?",
            "What relationships did you nurture or neglect?",
            "How did your habits trend over the month?",
            "What would you do differently next month?",
            "What are you most grateful for from this month?",
        ]

        quarterly_prompts = [
            "Are your goals still aligned with your values?",
            "What major accomplishments are you proud of?",
            "What patterns do you notice in your successes and struggles?",
            "What should you start, stop, or continue doing?",
            "How is your work-life balance?",
            "What's one big thing you want to accomplish next quarter?",
        ]

        if review_type == ReviewType.WEEKLY:
            return weekly_prompts
        elif review_type == ReviewType.MONTHLY:
            return monthly_prompts
        else:
            return quarterly_prompts

    # ========================================================================
    # REVIEW PERSISTENCE
    # ========================================================================

    def save_review(
        self,
        review_data: dict,
        reflections: Optional[Dict[str, str]] = None,
        next_week_focus: Optional[List[str]] = None,
    ) -> int:
        """
        Save a review to the database.

        Args:
            review_data: Generated review data
            reflections: User's reflection answers
            next_week_focus: List of focus items for next period

        Returns:
            Review ID
        """
        import json

        data = {
            "review_type": review_data.get("review_type", "weekly"),
            "period_start": review_data.get("period_start"),
            "period_end": review_data.get("period_end"),
            "summary": json.dumps(review_data),
            "reflections": json.dumps(reflections or {}),
            "next_week_focus": json.dumps(next_week_focus or []),
            "status": "draft",
        }

        review_id = self.db.insert(self.TABLE_NAME, data)

        self.event_store.emit(
            event_type="REVIEW_CREATED",
            entity_type="review",
            entity_id=review_id,
            payload={
                "review_type": data["review_type"],
                "period_start": data["period_start"],
                "period_end": data["period_end"],
            }
        )

        return review_id

    def complete_review(
        self,
        review_id: int,
        reflections: Dict[str, str],
        next_week_focus: List[str],
    ) -> bool:
        """
        Mark a review as completed with reflections.

        Args:
            review_id: Review ID
            reflections: User's reflection answers
            next_week_focus: Focus items for next period

        Returns:
            True if completed successfully
        """
        import json

        data = {
            "reflections": json.dumps(reflections),
            "next_week_focus": json.dumps(next_week_focus),
            "completed_at": datetime.now().isoformat(),
            "status": "completed",
        }

        result = self.db.update(self.TABLE_NAME, data, "id = ?", (review_id,))

        if result > 0:
            self.event_store.emit(
                event_type="REVIEW_COMPLETED",
                entity_type="review",
                entity_id=review_id,
                payload={"completed_at": data["completed_at"]}
            )
            return True
        return False

    def get_review(self, review_id: int) -> Optional[dict]:
        """Get a saved review by ID."""
        import json

        row = self.db.fetchone(
            f"SELECT * FROM {self.TABLE_NAME} WHERE id = ?",
            (review_id,)
        )

        if not row:
            return None

        review = dict(row)
        review["summary"] = json.loads(review.get("summary") or "{}")
        review["reflections"] = json.loads(review.get("reflections") or "{}")
        review["next_week_focus"] = json.loads(review.get("next_week_focus") or "[]")

        return review

    def list_reviews(
        self,
        review_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 20
    ) -> List[dict]:
        """List saved reviews."""
        import json

        conditions = []
        params = []

        if review_type:
            conditions.append("review_type = ?")
            params.append(review_type)
        if status:
            conditions.append("status = ?")
            params.append(status)

        where = " AND ".join(conditions) if conditions else "1=1"
        sql = f"""SELECT * FROM {self.TABLE_NAME}
                  WHERE {where} ORDER BY period_end DESC LIMIT ?"""
        params.append(limit)

        rows = self.db.fetchall(sql, tuple(params))

        reviews = []
        for row in rows:
            review = dict(row)
            review["summary"] = json.loads(review.get("summary") or "{}")
            review["reflections"] = json.loads(review.get("reflections") or "{}")
            review["next_week_focus"] = json.loads(review.get("next_week_focus") or "[]")
            reviews.append(review)

        return reviews

    def get_latest_review(self, review_type: str = "weekly") -> Optional[dict]:
        """Get the most recent review of a given type."""
        reviews = self.list_reviews(review_type=review_type, limit=1)
        return reviews[0] if reviews else None

    # ========================================================================
    # REVIEW ANALYTICS
    # ========================================================================

    def get_review_streak(self) -> int:
        """Get current weekly review streak (consecutive weeks)."""
        reviews = self.list_reviews(review_type="weekly", status="completed", limit=52)

        if not reviews:
            return 0

        streak = 0
        current_week = date.today().isocalendar()[:2]  # (year, week)

        for review in reviews:
            period_end = date.fromisoformat(review["period_end"])
            review_week = period_end.isocalendar()[:2]

            expected_week = (
                current_week[0],
                current_week[1] - streak
            )
            # Handle year boundary
            if expected_week[1] <= 0:
                expected_week = (expected_week[0] - 1, 52 + expected_week[1])

            if review_week == expected_week:
                streak += 1
            else:
                break

        return streak

    def get_trends(self, weeks: int = 4) -> dict:
        """Get trends across recent reviews."""
        reviews = self.list_reviews(review_type="weekly", status="completed", limit=weeks)

        if not reviews:
            return {"message": "No completed reviews yet"}

        # Extract metrics from each review
        task_completion = []
        goal_progress = []
        habit_rates = []

        for r in reviews:
            summary = r.get("summary", {})
            tasks = summary.get("tasks", {})
            goals = summary.get("goals", {})
            habits = summary.get("habits", {})

            task_completion.append(tasks.get("completion_rate", 0))
            goal_progress.append(goals.get("average_progress", 0))
            habit_rates.append(habits.get("average_weekly_rate", 0))

        # Calculate trends (positive = improving)
        def trend(values):
            if len(values) < 2:
                return 0
            return round(values[0] - values[-1], 1)

        return {
            "weeks_analyzed": len(reviews),
            "task_completion_trend": trend(task_completion),
            "goal_progress_trend": trend(goal_progress),
            "habit_rate_trend": trend(habit_rates),
            "review_streak": self.get_review_streak(),
        }
