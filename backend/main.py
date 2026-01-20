import sys
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional

from modules.life.task_tracker import TaskTracker, TaskPriority as TrackerPriority, TaskStatus as TrackerStatus
from backend.schemas import Task, TaskCreate, TaskUpdate, TaskStatus

app = FastAPI(title="Atlas Personal OS API")

# Configure CORS
origins = [
    "http://localhost:5173",  # Vite default port
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize TaskTracker
# We initialize it here. In a larger app we might use dependency injection.
tracker = TaskTracker()

@app.get("/")
def read_root():
    return {"message": "Welcome to Atlas Personal OS API"}

@app.get("/tasks", response_model=List[Task])
def list_tasks(status: Optional[TaskStatus] = None, category: Optional[str] = None):
    tracker_status = TrackerStatus(status.value) if status else None
    tasks = tracker.list(status=tracker_status, category=category)
    return tasks

@app.post("/tasks", response_model=Task, status_code=status.HTTP_201_CREATED)
def create_task(task: TaskCreate):
    tracker_priority = TrackerPriority(task.priority.value)
    task_id = tracker.add(
        title=task.title,
        description=task.description or "",
        priority=tracker_priority,
        category=task.category or "",
        due_date=task.due_date
    )
    
    # Retrieve the created task to return it
    # We might need to refactor TaskTracker.add to return the full task or fetch it here.
    # TaskTracker.get returns a dict.
    created_task = tracker.get(task_id)
    if not created_task:
        raise HTTPException(status_code=500, detail="Failed to create task")
    
    return created_task

@app.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: int):
    task = tracker.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.put("/tasks/{task_id}", response_model=Task)
def update_task(task_id: int, task_update: TaskUpdate):
    existing_task = tracker.get(task_id)
    if not existing_task:
        raise HTTPException(status_code=404, detail="Task not found")

    update_data = task_update.model_dump(exclude_unset=True)
    
    # Convert enums if present
    if "priority" in update_data:
         update_data["priority"] = TrackerPriority(update_data["priority"].value)
    if "status" in update_data:
        update_data["status"] = TrackerStatus(update_data["status"].value)
        
    if update_data:
        tracker.update(task_id, **update_data)
        
    return tracker.get(task_id)

@app.post("/tasks/{task_id}/complete", response_model=Task)
def complete_task(task_id: int):
    task = tracker.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    tracker.complete(task_id)
    return tracker.get(task_id)

@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int):
     task = tracker.get(task_id)
     if not task:
        raise HTTPException(status_code=404, detail="Task not found")
     tracker.delete(task_id)
     return None
