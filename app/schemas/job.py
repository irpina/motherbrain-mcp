from typing import Optional
from pydantic import BaseModel, ConfigDict


class JobCreate(BaseModel):
    type: str
    payload: dict
    requirements: list[str] = []
    parent_job: Optional[str] = None
    depends_on: list[str] = []
    priority: str = "medium"  # low/medium/high
    notes: list[dict] = []
    created_by: str = "admin"
    target_type: str = "agent"  # "agent" | "mcp"
    topic: Optional[str] = None


class JobResponse(BaseModel):
    job_id: str
    type: str
    payload: dict
    requirements: list
    status: str
    assigned_agent: Optional[str]
    parent_job: Optional[str]
    child_jobs: list
    depends_on: list
    priority: str
    notes: list
    created_by: str
    target_type: str
    result: Optional[dict]
    error: Optional[str]
    topic: Optional[str]
    model_config = ConfigDict(from_attributes=True)


class JobStatusUpdate(BaseModel):
    status: str  # "running" | "completed" | "failed"
    log: Optional[str] = None


class LogEntry(BaseModel):
    log: str


class NoteCreate(BaseModel):
    author: str
    content: str
