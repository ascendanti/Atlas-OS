"""
Atlas Personal OS - FastAPI Web Server v2.1

REST API for the web interface with endpoints for all modules.
Enhanced with GTD views, OKR support, and weekly reviews.

Run with: uvicorn modules.api.server:app --reload

Environment variables:
  ATLAS_CORS_ORIGINS: Comma-separated list of allowed origins
  ATLAS_ENV: "development" or "production"
"""

import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import date, timedelta

from modules.core.database import get_database
from modules.core.event_store import get_event_store

# Life modules
from modules.life.task_tracker import TaskTracker, TaskPriority, TaskStatus, RecurrenceType
from modules.life.goal_manager import GoalManager, AreaOfLife
from modules.life.contact_manager import ContactManager
from modules.life.habit_tracker import HabitTracker
from modules.life.event_reminder import EventReminder
from modules.life.weekly_review import WeeklyReview, ReviewType

# Knowledge modules
from modules.knowledge.note_manager import NoteManager
from modules.knowledge.pdf_indexer import PDFIndexer

# Content modules
from modules.content.idea_bank import IdeaBank
from modules.content.video_planner import VideoPlanner
from modules.content.podcast_scheduler import PodcastScheduler

# Career modules
from modules.career.publication_tracker import PublicationTracker
from modules.career.cv_manager import CVManager

# Financial modules
from modules.financial.portfolio_tracker import PortfolioTracker

app = FastAPI(
    title="Atlas Personal OS API",
    description="REST API for Atlas Personal OS - Enhanced with GTD & OKR",
    version="2.1.0"
)

# CORS Configuration
# Set ATLAS_CORS_ORIGINS env var for production (comma-separated)
# Example: ATLAS_CORS_ORIGINS=https://atlas.example.com,https://app.example.com
def get_cors_origins() -> list:
    """Get CORS origins from environment or use defaults."""
    env_origins = os.getenv("ATLAS_CORS_ORIGINS", "")
    if env_origins:
        return [origin.strip() for origin in env_origins.split(",") if origin.strip()]

    # Default development origins
    return [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:8000",
        "http://localhost:8000",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize all modules
db = get_database()
event_store = get_event_store()

task_tracker = TaskTracker(db=db, event_store=event_store)
goal_manager = GoalManager(db=db, event_store=event_store)
contact_manager = ContactManager(db=db)
habit_tracker = HabitTracker(db=db)
reminder_system = EventReminder(db=db, event_store=event_store)
note_manager = NoteManager(db=db, event_store=event_store)
pdf_indexer = PDFIndexer(db=db, event_store=event_store)
idea_bank = IdeaBank(db=db, event_store=event_store)
video_planner = VideoPlanner(db=db, event_store=event_store)
podcast_scheduler = PodcastScheduler(db=db, event_store=event_store)
publication_tracker = PublicationTracker(db=db, event_store=event_store)
cv_manager = CVManager(db=db, event_store=event_store)
portfolio_tracker = PortfolioTracker(db=db)
weekly_review = WeeklyReview(db=db, event_store=event_store)


# ============================================================================
# REQUEST MODELS
# ============================================================================

class TaskCreate(BaseModel):
    title: str
    description: str = ""
    priority: str = "MEDIUM"
    due_date: Optional[str] = None
    scheduled_date: Optional[str] = None
    tags: List[str] = []
    estimated_minutes: Optional[int] = None
    recurrence_type: str = "none"
    context: str = ""
    energy_level: str = ""
    goal_id: Optional[int] = None

class SubtaskCreate(BaseModel):
    title: str
    description: str = ""

class TimeLogEntry(BaseModel):
    minutes: int

class GoalCreate(BaseModel):
    title: str
    description: str = ""
    area: str = "other"
    target_date: Optional[str] = None
    target_value: int = 100
    parent_id: Optional[int] = None

class KeyResultCreate(BaseModel):
    title: str
    target_value: int = 100
    unit: str = "%"
    description: str = ""

class MilestoneCreate(BaseModel):
    title: str
    target_date: Optional[str] = None
    description: str = ""

class ProgressUpdate(BaseModel):
    value: int
    note: str = ""
    reflection: str = ""

class ReviewComplete(BaseModel):
    reflections: dict
    next_week_focus: List[str]


# ============================================================================
# DASHBOARD
# ============================================================================

@app.get("/api/dashboard")
def get_dashboard():
    """Get enhanced dashboard with GTD metrics."""
    tasks = task_tracker.list(limit=1000)
    pending_tasks = len([t for t in tasks if t["status"] == "pending"])
    overdue_tasks = len(task_tracker.get_overdue())
    today_tasks = len(task_tracker.get_today())

    goals = goal_manager.list_goals(limit=1000)
    active_goals = len([g for g in goals if g.get("status") == "active"])

    habits_today = habit_tracker.get_today_status()
    habits_done = len([h for h in habits_today if h["completed_today"]]) if habits_today else 0

    reminders = reminder_system.upcoming(days=7)
    notes = note_manager.list_notes()
    ideas = idea_bank.list_ideas()
    videos = video_planner.list_videos()
    podcasts = podcast_scheduler.list_episodes()
    publications = publication_tracker.list_publications()
    cv_entries = cv_manager.list_entries()
    contacts = contact_manager.list()

    # Get review streak
    review_streak = weekly_review.get_review_streak()

    return {
        "tasks": {
            "pending": pending_tasks,
            "overdue": overdue_tasks,
            "due_today": today_tasks,
            "total": len(tasks)
        },
        "goals": {"active": active_goals, "total": len(goals)},
        "habits": {
            "completed_today": habits_done,
            "total": len(habits_today) if habits_today else 0
        },
        "reminders": {"upcoming_week": len(reminders)},
        "notes": {"total": len(notes)},
        "ideas": {"total": len(ideas)},
        "videos": {"total": len(videos)},
        "podcasts": {"total": len(podcasts)},
        "publications": {"total": len(publications)},
        "cv_entries": {"total": len(cv_entries)},
        "contacts": {"total": len(contacts)},
        "review_streak": review_streak,
    }


# ============================================================================
# TASKS - Enhanced
# ============================================================================

def _format_task(t: dict) -> dict:
    """Format task for API response."""
    priority_names = {1: "LOW", 2: "MEDIUM", 3: "HIGH", 4: "URGENT"}
    return {
        "id": t["id"],
        "title": t["title"],
        "description": t.get("description", ""),
        "status": t["status"],
        "priority": priority_names.get(t["priority"], "MEDIUM"),
        "tags": t.get("tags", []),
        "due_date": t.get("due_date") or "",
        "scheduled_date": t.get("scheduled_date") or "",
        "estimated_minutes": t.get("estimated_minutes"),
        "actual_minutes": t.get("actual_minutes", 0),
        "recurrence_type": t.get("recurrence_type", "none"),
        "context": t.get("context", ""),
        "energy_level": t.get("energy_level", ""),
        "parent_id": t.get("parent_id"),
        "goal_id": t.get("goal_id"),
        "blocked_by": t.get("blocked_by", []),
    }

@app.get("/api/tasks")
def list_tasks(
    status: Optional[str] = None,
    tag: Optional[str] = None,
    goal_id: Optional[int] = None,
    limit: int = 100
):
    """List all tasks with filters."""
    tasks = task_tracker.list(status=status, tag=tag, goal_id=goal_id, limit=limit)
    return [_format_task(t) for t in tasks]

@app.get("/api/tasks/today")
def get_tasks_today():
    """GTD: Get tasks due or scheduled for today."""
    tasks = task_tracker.get_today()
    return [_format_task(t) for t in tasks]

@app.get("/api/tasks/upcoming")
def get_tasks_upcoming(days: int = 7):
    """GTD: Get tasks due in the next N days."""
    tasks = task_tracker.get_upcoming(days=days)
    return [_format_task(t) for t in tasks]

@app.get("/api/tasks/overdue")
def get_tasks_overdue():
    """GTD: Get overdue tasks."""
    tasks = task_tracker.get_overdue()
    return [_format_task(t) for t in tasks]

@app.get("/api/tasks/someday")
def get_tasks_someday():
    """GTD: Get someday/maybe tasks."""
    tasks = task_tracker.get_someday()
    return [_format_task(t) for t in tasks]

@app.get("/api/tasks/blocked")
def get_tasks_blocked():
    """Get blocked tasks."""
    tasks = task_tracker.get_blocked()
    return [_format_task(t) for t in tasks]

@app.get("/api/tasks/by-context/{context}")
def get_tasks_by_context(context: str):
    """Get tasks by context (e.g., @home, @work)."""
    tasks = task_tracker.get_by_context(context)
    return [_format_task(t) for t in tasks]

@app.get("/api/tasks/by-energy/{energy_level}")
def get_tasks_by_energy(energy_level: str):
    """Get tasks by energy level (low, medium, high)."""
    tasks = task_tracker.get_by_energy(energy_level)
    return [_format_task(t) for t in tasks]

@app.get("/api/tasks/stats")
def get_task_stats():
    """Get task statistics."""
    return task_tracker.get_stats()

@app.get("/api/tasks/tags")
def get_all_tags():
    """Get all unique tags."""
    return task_tracker.get_all_tags()

@app.get("/api/tasks/{task_id}")
def get_task(task_id: int):
    """Get a single task by ID."""
    task = task_tracker.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return _format_task(task)

@app.get("/api/tasks/{task_id}/subtasks")
def get_subtasks(task_id: int):
    """Get subtasks of a task."""
    subtasks = task_tracker.get_subtasks(task_id)
    return [_format_task(t) for t in subtasks]

@app.post("/api/tasks")
def create_task(task: TaskCreate):
    """Create a new task with all options."""
    task_id = task_tracker.add(
        title=task.title,
        description=task.description,
        priority=TaskPriority[task.priority.upper()],
        due_date=date.fromisoformat(task.due_date) if task.due_date else None,
        scheduled_date=date.fromisoformat(task.scheduled_date) if task.scheduled_date else None,
        tags=task.tags,
        estimated_minutes=task.estimated_minutes,
        recurrence_type=RecurrenceType(task.recurrence_type),
        context=task.context,
        energy_level=task.energy_level,
        goal_id=task.goal_id,
    )
    return {"id": task_id}

@app.post("/api/tasks/{task_id}/subtasks")
def create_subtask(task_id: int, subtask: SubtaskCreate):
    """Add a subtask to a task."""
    try:
        sub_id = task_tracker.add_subtask(task_id, subtask.title, description=subtask.description)
        return {"id": sub_id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/api/tasks/{task_id}/complete")
def complete_task(task_id: int):
    """Mark task as completed."""
    if not task_tracker.complete(task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "completed"}

@app.post("/api/tasks/{task_id}/time")
def log_task_time(task_id: int, entry: TimeLogEntry):
    """Log time spent on a task."""
    if not task_tracker.log_time(task_id, entry.minutes):
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "time logged"}

@app.post("/api/tasks/{task_id}/tags/{tag}")
def add_task_tag(task_id: int, tag: str):
    """Add a tag to a task."""
    if not task_tracker.add_tag(task_id, tag):
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "tag added"}

@app.delete("/api/tasks/{task_id}/tags/{tag}")
def remove_task_tag(task_id: int, tag: str):
    """Remove a tag from a task."""
    if not task_tracker.remove_tag(task_id, tag):
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "tag removed"}

@app.post("/api/tasks/{task_id}/depends-on/{blocker_id}")
def add_task_dependency(task_id: int, blocker_id: int):
    """Add a dependency (task blocked by another task)."""
    if not task_tracker.add_dependency(task_id, blocker_id):
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "dependency added"}

@app.delete("/api/tasks/{task_id}/depends-on/{blocker_id}")
def remove_task_dependency(task_id: int, blocker_id: int):
    """Remove a dependency."""
    if not task_tracker.remove_dependency(task_id, blocker_id):
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "dependency removed"}

@app.post("/api/tasks/{task_id}/link-goal/{goal_id}")
def link_task_to_goal(task_id: int, goal_id: int):
    """Link a task to a goal."""
    if not task_tracker.link_to_goal(task_id, goal_id):
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "linked to goal"}


# ============================================================================
# GOALS - Enhanced with OKR
# ============================================================================

def _format_goal(g: dict) -> dict:
    """Format goal for API response."""
    return {
        "id": g["id"],
        "title": g["title"],
        "description": g.get("description", ""),
        "area": g.get("area", "other"),
        "status": g.get("status", "active"),
        "target_date": g.get("target_date") or "",
        "target_value": g.get("target_value", 100),
        "current_value": g.get("current_value", 0),
        "parent_id": g.get("parent_id"),
        "created_at": g.get("created_at", ""),
    }

@app.get("/api/goals")
def list_goals(
    area: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100
):
    """List all goals with filters."""
    area_enum = AreaOfLife(area) if area else None
    goals = goal_manager.list_goals(limit=limit, area=area_enum, status=status)
    result = []
    for g in goals:
        progress = goal_manager.progress(g["id"])
        goal_data = _format_goal(g)
        goal_data["percentage"] = progress["percentage"] if progress else 0
        goal_data["key_results_count"] = progress.get("key_results", {}).get("count", 0) if progress else 0
        goal_data["milestones_completed"] = progress.get("milestones", {}).get("completed", 0) if progress else 0
        goal_data["milestones_total"] = progress.get("milestones", {}).get("total", 0) if progress else 0
        result.append(goal_data)
    return result

@app.get("/api/goals/areas")
def get_goal_areas():
    """Get all areas of life."""
    return [{"value": a.value, "label": a.name.replace("_", " ").title()} for a in AreaOfLife]

@app.get("/api/goals/top-level")
def get_top_level_goals():
    """Get goals with no parent (top-level objectives)."""
    goals = goal_manager.get_top_level_goals()
    return [_format_goal(g) for g in goals]

@app.get("/api/goals/by-area/{area}")
def get_goals_by_area(area: str):
    """Get goals by area of life."""
    goals = goal_manager.get_by_area(AreaOfLife(area))
    return [_format_goal(g) for g in goals]

@app.get("/api/goals/stats")
def get_goal_stats():
    """Get goal statistics by area."""
    return goal_manager.get_stats()

@app.get("/api/goals/{goal_id}")
def get_goal(goal_id: int):
    """Get a single goal with full details."""
    goal = goal_manager.get(goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    progress = goal_manager.progress(goal_id)
    key_results = goal_manager.get_key_results(goal_id)
    milestones = goal_manager.get_milestones(goal_id)
    children = goal_manager.get_children(goal_id)
    history = goal_manager.get_progress_history(goal_id)

    return {
        **_format_goal(goal),
        "progress": progress,
        "key_results": key_results,
        "milestones": milestones,
        "children": [_format_goal(c) for c in children],
        "history": history,
    }

@app.get("/api/goals/{goal_id}/children")
def get_goal_children(goal_id: int):
    """Get child goals of a parent goal."""
    children = goal_manager.get_children(goal_id)
    return [_format_goal(c) for c in children]

@app.get("/api/goals/{goal_id}/key-results")
def get_goal_key_results(goal_id: int):
    """Get Key Results for a goal (OKR)."""
    return goal_manager.get_key_results(goal_id)

@app.get("/api/goals/{goal_id}/milestones")
def get_goal_milestones(goal_id: int):
    """Get milestones for a goal."""
    return goal_manager.get_milestones(goal_id)

@app.get("/api/goals/{goal_id}/tasks")
def get_goal_tasks(goal_id: int):
    """Get all tasks linked to a goal."""
    tasks = task_tracker.get_tasks_for_goal(goal_id)
    return [_format_task(t) for t in tasks]

@app.get("/api/goals/{goal_id}/history")
def get_goal_history(goal_id: int):
    """Get progress history for a goal."""
    return goal_manager.get_progress_history(goal_id)

@app.post("/api/goals")
def create_goal(goal: GoalCreate):
    """Create a new goal/objective."""
    area_enum = AreaOfLife(goal.area) if goal.area else AreaOfLife.OTHER
    target_date_parsed = date.fromisoformat(goal.target_date) if goal.target_date else None

    goal_id = goal_manager.define(
        title=goal.title,
        description=goal.description,
        area=area_enum,
        target_date=target_date_parsed,
        target_value=goal.target_value,
        parent_id=goal.parent_id,
    )
    return {"id": goal_id}

@app.post("/api/goals/{goal_id}/key-results")
def add_key_result(goal_id: int, kr: KeyResultCreate):
    """Add a Key Result to a goal (OKR)."""
    kr_id = goal_manager.add_key_result(
        goal_id=goal_id,
        title=kr.title,
        target_value=kr.target_value,
        unit=kr.unit,
        description=kr.description,
    )
    if kr_id is None:
        raise HTTPException(status_code=404, detail="Goal not found")
    return {"id": kr_id}

@app.post("/api/goals/{goal_id}/milestones")
def add_milestone(goal_id: int, ms: MilestoneCreate):
    """Add a milestone to a goal."""
    target_date_parsed = date.fromisoformat(ms.target_date) if ms.target_date else None
    ms_id = goal_manager.add_milestone(
        goal_id=goal_id,
        title=ms.title,
        target_date=target_date_parsed,
        description=ms.description,
    )
    if ms_id is None:
        raise HTTPException(status_code=404, detail="Goal not found")
    return {"id": ms_id}

@app.post("/api/goals/{goal_id}/progress")
def log_goal_progress(goal_id: int, update: ProgressUpdate):
    """Log progress on a goal with optional reflection."""
    if not goal_manager.log_progress(goal_id, update.value, update.note, update.reflection):
        raise HTTPException(status_code=404, detail="Goal not found")
    return {"message": "progress logged"}

@app.put("/api/key-results/{kr_id}")
def update_key_result(kr_id: int, update: ProgressUpdate):
    """Update a Key Result's progress."""
    if not goal_manager.update_key_result(kr_id, update.value, update.note):
        raise HTTPException(status_code=404, detail="Key Result not found")
    return {"message": "key result updated"}

@app.post("/api/milestones/{ms_id}/complete")
def complete_milestone(ms_id: int):
    """Mark a milestone as completed."""
    if not goal_manager.complete_milestone(ms_id):
        raise HTTPException(status_code=404, detail="Milestone not found or already completed")
    return {"message": "milestone completed"}

@app.post("/api/goals/{goal_id}/archive")
def archive_goal(goal_id: int):
    """Archive a goal."""
    if not goal_manager.archive(goal_id):
        raise HTTPException(status_code=404, detail="Goal not found or already archived")
    return {"message": "goal archived"}


# ============================================================================
# WEEKLY REVIEW
# ============================================================================

@app.get("/api/reviews/generate")
def generate_review(review_type: str = "weekly"):
    """Generate a new review report."""
    rt = ReviewType(review_type)
    return weekly_review.generate_review(review_type=rt)

@app.get("/api/reviews")
def list_reviews(
    review_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 20
):
    """List saved reviews."""
    return weekly_review.list_reviews(review_type=review_type, status=status, limit=limit)

@app.get("/api/reviews/latest")
def get_latest_review(review_type: str = "weekly"):
    """Get the most recent review."""
    review = weekly_review.get_latest_review(review_type=review_type)
    if not review:
        raise HTTPException(status_code=404, detail="No reviews found")
    return review

@app.get("/api/reviews/trends")
def get_review_trends(weeks: int = 4):
    """Get trends across recent reviews."""
    return weekly_review.get_trends(weeks=weeks)

@app.get("/api/reviews/streak")
def get_review_streak():
    """Get current weekly review streak."""
    return {"streak": weekly_review.get_review_streak()}

@app.get("/api/reviews/{review_id}")
def get_review(review_id: int):
    """Get a saved review by ID."""
    review = weekly_review.get_review(review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    return review

@app.post("/api/reviews")
def save_review(review_data: dict):
    """Save a generated review."""
    review_id = weekly_review.save_review(review_data)
    return {"id": review_id}

@app.post("/api/reviews/{review_id}/complete")
def complete_review(review_id: int, completion: ReviewComplete):
    """Complete a review with reflections."""
    if not weekly_review.complete_review(review_id, completion.reflections, completion.next_week_focus):
        raise HTTPException(status_code=404, detail="Review not found")
    return {"message": "review completed"}


# ============================================================================
# REMINDERS
# ============================================================================

@app.get("/api/reminders")
def list_reminders(days: Optional[int] = None, limit: int = 100):
    if days:
        reminders = reminder_system.upcoming(days=days)
    else:
        reminders = reminder_system.list_reminders(limit=limit)
    return [{"id": r["id"], "title": r["title"], "event_date": r["event_date"],
             "event_time": r["event_time"] or "", "recurrence": r["recurrence"],
             "completed": r["completed"]} for r in reminders]

@app.post("/api/reminders")
def create_reminder(title: str, event_date: str, event_time: str = "", reminder_minutes: int = 30):
    reminder_id = reminder_system.add(title=title, event_date=event_date,
                                       event_time=event_time, reminder_minutes=reminder_minutes)
    return {"id": reminder_id}

@app.post("/api/reminders/{reminder_id}/complete")
def complete_reminder(reminder_id: int):
    if not reminder_system.complete(reminder_id):
        raise HTTPException(status_code=404, detail="Reminder not found")
    return {"message": "completed"}


# ============================================================================
# HABITS
# ============================================================================

@app.get("/api/habits")
def list_habits():
    habits = habit_tracker.list_habits()
    today_status = habit_tracker.get_today_status()
    status_map = {h["id"]: h for h in today_status} if today_status else {}
    return [{
        "id": h["id"], "name": h["name"], "frequency": h["frequency"],
        "target_count": h["target_count"],
        "completed_today": status_map.get(h["id"], {}).get("completed_today", False),
        "current_streak": status_map.get(h["id"], {}).get("current_streak", 0)
    } for h in habits]

@app.post("/api/habits/{habit_id}/complete")
def complete_habit(habit_id: int):
    habit_tracker.complete_habit(habit_id)
    return {"message": "completed"}


# ============================================================================
# CONTACTS
# ============================================================================

@app.get("/api/contacts")
def list_contacts(category: Optional[str] = None, limit: int = 100):
    contacts = contact_manager.list(limit=limit)
    return [{"id": c["id"], "first_name": c["first_name"], "last_name": c["last_name"] or "",
             "email": c["email"] or "", "phone": c["phone"] or "",
             "category": c["category"] or ""} for c in contacts]


# ============================================================================
# NOTES
# ============================================================================

@app.get("/api/notes")
def list_notes(query: Optional[str] = None, limit: int = 100):
    if query:
        notes = note_manager.search(query, limit=limit)
    else:
        notes = note_manager.list_notes(limit=limit)
    return [{"id": n["id"], "title": n["title"],
             "tags": ",".join(n["tags"]) if isinstance(n["tags"], list) else (n["tags"] or ""),
             "archived": n.get("archived", False)} for n in notes]

@app.get("/api/notes/{note_id}")
def get_note(note_id: int):
    note = note_manager.get(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


# ============================================================================
# IDEAS
# ============================================================================

@app.get("/api/ideas")
def list_ideas(platform: Optional[str] = None, status: Optional[str] = None, limit: int = 100):
    ideas = idea_bank.list_ideas(limit=limit)
    return [{"id": i["id"], "title": i["title"], "platform": i["platform"],
             "status": i["status"], "priority": i["priority"]} for i in ideas]


# ============================================================================
# VIDEOS
# ============================================================================

@app.get("/api/videos")
def list_videos(status: Optional[str] = None, limit: int = 100):
    videos = video_planner.list_videos(limit=limit)
    return [{"id": v["id"], "title": v["title"], "status": v["status"],
             "duration_estimate": v.get("duration_estimate") or 0} for v in videos]


# ============================================================================
# PODCASTS
# ============================================================================

@app.get("/api/podcasts")
def list_podcasts(status: Optional[str] = None, limit: int = 100):
    episodes = podcast_scheduler.list_episodes(limit=limit)
    return [{"id": e["id"], "title": e["title"], "status": e["status"],
             "episode_number": e.get("episode_number") or 0,
             "guest": e.get("guest") or ""} for e in episodes]


# ============================================================================
# PUBLICATIONS
# ============================================================================

@app.get("/api/publications")
def list_publications(status: Optional[str] = None, limit: int = 100):
    pubs = publication_tracker.list_publications(limit=limit)
    return [{"id": p["id"], "title": p["title"], "status": p["status"],
             "venue": p["venue"], "authors": p.get("authors") or ""} for p in pubs]


# ============================================================================
# CV ENTRIES
# ============================================================================

@app.get("/api/cv")
def list_cv_entries(entry_type: Optional[str] = None, limit: int = 100):
    entries = cv_manager.list_entries(limit=limit)
    return [{"id": e["id"], "title": e["title"], "entry_type": e["entry_type"],
             "organization": e.get("organization") or "",
             "start_date": e.get("start_date") or "",
             "end_date": e.get("end_date") or ""} for e in entries]


# ============================================================================
# PDFS
# ============================================================================

@app.get("/api/pdfs")
def list_pdfs(category: Optional[str] = None, limit: int = 100):
    pdfs = pdf_indexer.list_pdfs(limit=limit)
    return [{"id": p["id"], "title": p["title"], "category": p["category"],
             "authors": p.get("authors") or "", "page_count": p.get("page_count") or 0} for p in pdfs]


# ============================================================================
# PORTFOLIO
# ============================================================================

@app.get("/api/portfolio")
def get_portfolio():
    summary = portfolio_tracker.get_portfolio_summary()
    return {
        "holdings_count": summary["holdings_count"],
        "total_cost": summary["total_cost"],
        "total_value": summary["total_value"],
        "gain_loss": summary["total_gain_loss"],
        "gain_loss_percent": summary["total_gain_loss_percent"],
        "holdings": summary["holdings"]
    }


# ============================================================================
# EVENTS (AUDIT)
# ============================================================================

@app.get("/api/events")
def list_events(entity_type: Optional[str] = None, limit: int = 100):
    events = event_store.query(entity_type=entity_type, limit=limit)
    return events


# ============================================================================
# HEALTH
# ============================================================================

@app.get("/api/health")
def health_check():
    return {"status": "healthy", "service": "atlas-api", "version": "2.1.0"}


def run_server(host: str = "127.0.0.1", port: int = 8000):
    import uvicorn
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    run_server()
