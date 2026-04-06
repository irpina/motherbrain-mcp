from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Integer, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class AgentAction(Base):
    __tablename__ = "agent_actions"
    
    action_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    agent_id: Mapped[str] = mapped_column(String)
    action_type: Mapped[str] = mapped_column(String)
    job_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
