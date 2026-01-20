from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime
from enum import Enum

class TaskPriority(int, Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = ""
    priority: TaskPriority = TaskPriority.MEDIUM
    category: Optional[str] = ""
    due_date: Optional[date] = None

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[TaskPriority] = None
    category: Optional[str] = None
    due_date: Optional[date] = None
    status: Optional[TaskStatus] = None

class Task(TaskBase):
    id: int
    status: TaskStatus
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
