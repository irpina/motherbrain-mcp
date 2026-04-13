from __future__ import annotations
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class SpawnedAgent(Base):
    """Track spawned agent containers.
    
    When an admin spawns an agent from the UI, motherbrain launches a Docker
    container and tracks it here. The container_id is the Docker container ID
    for management (logs, kill, etc).
    
    Extension Points:
        - Add container resource limits (CPU, memory)
        - Add spawn reason/task tracking
        - Add auto-restart policy
        - Add cost/usage tracking
    """
    
    __tablename__ = "spawned_agents"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    agent_type: Mapped[str] = mapped_column(String, index=True)  # claude, codex, gemini
    container_id: Mapped[str] = mapped_column(String, unique=True)
    channel: Mapped[str] = mapped_column(String)  # Channel the agent joined
    status: Mapped[str] = mapped_column(String, default="running")  # running, stopped, error
    task: Mapped[str | None] = mapped_column(String, nullable=True)  # Initial task/prompt
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    stopped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
