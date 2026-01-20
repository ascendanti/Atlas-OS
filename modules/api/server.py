"""
Atlas Personal OS - FastAPI Web Server

REST API for the web interface. Provides endpoints for:
- Tasks (list, add, complete)
- Events (audit log)
- Goals (list, progress)
- Notes (list, search)

Run with: uvicorn modules.api.server:app --reload
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from modules.core.database import get_database
from modules.core.event_store import get_event_store
from modules.life.task_tracker import TaskTracker, TaskPriority
from modules.life.goal_manager import GoalManager
from modules.knowledge.note_manager import NoteManager

app = FastAPI(
    title="Atlas Personal OS API",
    description="REST API for Atlas Personal OS",
    version="1.0.0"
)

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize modules
db = get_database()
event_store = get_event_store()
task_tracker = TaskTracker(db=db, event_store=event_store)
goal_manager = GoalManager(db=db, event_store=event_store)
note_manager = NoteManager(db=db, event_store=event_store)


# Request models
class TaskCreate(BaseModel):
    title: str
    priority: str = "MEDIUM"
    category: str = ""


class GoalCreate(BaseModel):
    title: str
    target_date: Optional[str] = None


class NoteCreate(BaseModel):
    title: str
    content: str = ""
    tags: str = ""


# Tasks endpoints
@app.get("/api/tasks")
def list_tasks(status: Optional[str] = None, limit: int = 100):
    """List all tasks."""
    tasks = task_tracker.list(status=status, limit=limit)
    priority_names = {1: "LOW", 2: "MEDIUM", 3: "HIGH", 4: "URGENT"}
    return [
        {
            "id": t["id"],
            "title": t["title"],
            "status": t["status"],
            "priority": priority_names.get(t["priority"], "MEDIUM"),
            "category": t["category"] or "",
            "due_date": t["due_date"] or ""
        }
        for t in tasks
    ]


@app.post("/api/tasks")
def create_task(task: TaskCreate):
    """Create a new task."""
    priority = TaskPriority[task.priority.upper()]
    task_id = task_tracker.add(
        title=task.title,
        priority=priority,
        category=task.category
    )
    return {"id": task_id, "message": "Task created"}


@app.post("/api/tasks/{task_id}/complete")
def complete_task(task_id: int):
    """Mark a task as completed."""
    result = task_tracker.complete(task_id)
    if not result:
        raise HTTPException(status_code=404, detail="Task not found or already completed")
    return {"message": "Task completed"}


# Events endpoints
@app.get("/api/events")
def list_events(
    entity_type: Optional[str] = None,
    event_type: Optional[str] = None,
    limit: int = 100
):
    """List recent events from the audit log."""
    events = event_store.query(
        entity_type=entity_type,
        event_type=event_type,
        limit=limit
    )
    return events


@app.get("/api/events/{entity_type}/{entity_id}")
def explain_entity(entity_type: str, entity_id: int):
    """Get full event history for an entity."""
    events = event_store.explain(entity_type, entity_id)
    return events


# Goals endpoints
@app.get("/api/goals")
def list_goals(limit: int = 100):
    """List all goals."""
    goals = goal_manager.list_goals(limit=limit)
    return [
        {
            "id": g["id"],
            "title": g["title"],
            "target_date": g["target_date"] or "",
            "progress": g.get("progress", 0)
        }
        for g in goals
    ]


@app.post("/api/goals")
def create_goal(goal: GoalCreate):
    """Define a new goal."""
    goal_id = goal_manager.define(goal.title)
    if goal.target_date:
        goal_manager.set_target(goal_id, goal.target_date)
    return {"id": goal_id, "message": "Goal created"}


@app.get("/api/goals/{goal_id}/progress")
def get_goal_progress(goal_id: int):
    """Get progress for a specific goal."""
    progress = goal_manager.progress(goal_id)
    if progress is None:
        raise HTTPException(status_code=404, detail="Goal not found")
    return progress


# Notes endpoints
@app.get("/api/notes")
def list_notes(query: Optional[str] = None, limit: int = 100):
    """List or search notes."""
    if query:
        notes = note_manager.search(query, limit=limit)
    else:
        notes = note_manager.list_notes(limit=limit)
    return [
        {
            "id": n["id"],
            "title": n["title"],
            "tags": n["tags"] or "",
            "created_at": n.get("created_at", "")
        }
        for n in notes
    ]


@app.get("/api/notes/{note_id}")
def get_note(note_id: int):
    """Get a specific note with full content."""
    note = note_manager.get(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@app.post("/api/notes")
def create_note(note: NoteCreate):
    """Create a new note."""
    note_id = note_manager.create(
        title=note.title,
        content=note.content,
        tags=note.tags
    )
    return {"id": note_id, "message": "Note created"}


# Health check
@app.get("/api/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "atlas-api"}


def run_server(host: str = "127.0.0.1", port: int = 8000):
    """Run the API server."""
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()
