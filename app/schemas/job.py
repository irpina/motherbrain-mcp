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
    target_service_id: Optional[str] = None
    topic: Optional[str] = None
    assigned_agent: Optional[str] = None  # Pre-assign to specific agent (e.g., from @mention)
    context_job_ids: list[str] = []  # References to prior jobs for context
    skill_key: Optional[str] = None  # Key from context/skills store


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
    target_service_id: Optional[str]
    result: Optional[dict]
    error: Optional[str]
    topic: Optional[str]
    context_job_ids: list  # Stored references to prior jobs
    skill_key: Optional[str]  # Key from context/skills store
    model_config = ConfigDict(from_attributes=True)


class ContextJobInfo(BaseModel):
    """Lightweight info about a context job."""
    job_id: str
    type: str
    status: str
    result: Optional[dict]
    payload: dict


class JobDetail(JobResponse):
    """Enriched job response with hydrated context references."""
    context_jobs: list[ContextJobInfo] = []  # Hydrated context job details
    skill: Optional[dict] = None  # Full value from project_context for skill_key


class JobStatusUpdate(BaseModel):
    status: str  # "running" | "completed" | "failed"
    log: Optional[str] = None


class LogEntry(BaseModel):
    log: str


class NoteCreate(BaseModel):
    author: str
    content: str
