"""
Atlas Personal OS - FastAPI Web Server

REST API for the web interface with endpoints for all modules.
Run with: uvicorn modules.api.server:app --reload
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from datetime import date, timedelta

from modules.core.database import get_database
from modules.core.event_store import get_event_store

# Life modules
from modules.life.task_tracker import TaskTracker, TaskPriority
from modules.life.goal_manager import GoalManager
from modules.life.contact_manager import ContactManager
from modules.life.habit_tracker import HabitTracker
from modules.life.event_reminder import EventReminder

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
    description="REST API for Atlas Personal OS - All Modules",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
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


# ============================================================================
# DASHBOARD
# ============================================================================

@app.get("/api/dashboard")
def get_dashboard():
    """Get dashboard summary of all modules."""
    tasks = task_tracker.list(limit=1000)
    pending_tasks = len([t for t in tasks if t["status"] == "pending"])

    goals = goal_manager.list_goals(limit=1000)
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

    return {
        "tasks": {"pending": pending_tasks, "total": len(tasks)},
        "goals": {"active": len(goals)},
        "habits": {"completed_today": habits_done, "total": len(habits_today) if habits_today else 0},
        "reminders": {"upcoming_week": len(reminders)},
        "notes": {"total": len(notes)},
        "ideas": {"total": len(ideas)},
        "videos": {"total": len(videos)},
        "podcasts": {"total": len(podcasts)},
        "publications": {"total": len(publications)},
        "cv_entries": {"total": len(cv_entries)},
        "contacts": {"total": len(contacts)},
    }


# ============================================================================
# TASKS
# ============================================================================

@app.get("/api/tasks")
def list_tasks(status: Optional[str] = None, limit: int = 100):
    tasks = task_tracker.list(status=status, limit=limit)
    priority_names = {1: "LOW", 2: "MEDIUM", 3: "HIGH", 4: "URGENT"}
    return [{"id": t["id"], "title": t["title"], "status": t["status"],
             "priority": priority_names.get(t["priority"], "MEDIUM"),
             "category": t["category"] or "", "due_date": t["due_date"] or ""} for t in tasks]

@app.post("/api/tasks")
def create_task(title: str, priority: str = "MEDIUM", category: str = ""):
    task_id = task_tracker.add(title=title, priority=TaskPriority[priority.upper()], category=category)
    return {"id": task_id}

@app.post("/api/tasks/{task_id}/complete")
def complete_task(task_id: int):
    if not task_tracker.complete(task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "completed"}


# ============================================================================
# GOALS
# ============================================================================

@app.get("/api/goals")
def list_goals(limit: int = 100):
    goals = goal_manager.list_goals(limit=limit)
    result = []
    for g in goals:
        progress = goal_manager.progress(g["id"])
        result.append({
            "id": g["id"], "title": g["title"],
            "target_date": g.get("target_date") or "",
            "percentage": progress["percentage"] if progress else 0,
            "status": progress["status"] if progress else "active"
        })
    return result

@app.post("/api/goals")
def create_goal(title: str, target_date: Optional[str] = None):
    goal_id = goal_manager.define(title)
    if target_date:
        goal_manager.set_target(goal_id, target_date)
    return {"id": goal_id}


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
    return {"status": "healthy", "service": "atlas-api", "version": "2.0.0"}


def run_server(host: str = "127.0.0.1", port: int = 8000):
    import uvicorn
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    run_server()
