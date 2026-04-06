from __future__ import annotations
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import String, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class Agent(Base):
    """Agent registration and state model.
    
    Represents a registered AI agent (like Kimi CLI or Claude CLI) that
    can claim and execute jobs.
    
    Extension Points:
        - Add performance metrics (jobs_completed, avg_execution_time)
        - Add resource limits (max_concurrent_jobs)
        - Add agent groups/roles for RBAC
    """
    
    # TODO: Add job execution statistics
    # TODO: Add concurrent job limit
    # TODO: Add agent groups for multi-tenant support
    __tablename__ = "agents"

    agent_id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    platform: Mapped[str] = mapped_column(String)
    capabilities: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String, default="online")
    last_heartbeat: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    token: Mapped[str] = mapped_column(String, unique=True)
