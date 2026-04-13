from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4
from sqlalchemy import String, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class Job(Base):
    """Job/Task model for agent and MCP service execution.
    
    This model represents a unit of work that can be assigned to either
    an agent or an MCP service based on target_type.
    
    Extension Points:
        - Add scheduling fields (scheduled_at, run_after)
        - Add retry configuration (max_retries, retry_count)
        - Add priority weighting for queue ordering
    """
    
    # TODO: Add scheduling support for delayed job execution
    # TODO: Add retry logic fields for failed jobs
    # TODO: Add job dependencies (depends_on as foreign keys)
    __tablename__ = "jobs"

    job_id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    type: Mapped[str] = mapped_column(String)
    payload: Mapped[dict] = mapped_column(JSON)
    requirements: Mapped[list] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String, default="pending")
    assigned_agent: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Hierarchy and dependency fields
    parent_job: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    child_jobs: Mapped[list] = mapped_column(JSON, default=list)
    depends_on: Mapped[list] = mapped_column(JSON, default=list)
    priority: Mapped[str] = mapped_column(String, default="medium")  # low/medium/high
    notes: Mapped[list] = mapped_column(JSON, default=list)
    created_by: Mapped[str] = mapped_column(String, default="admin")
    
    # MCP routing fields
    target_type: Mapped[str] = mapped_column(String, default="agent")  # "agent" | "mcp"
    target_service_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    result: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    topic: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    # Context references for agent context
    context_job_ids: Mapped[list] = mapped_column(JSON, default=list)
    skill_key: Mapped[Optional[str]] = mapped_column(String, nullable=True)
