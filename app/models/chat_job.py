from __future__ import annotations
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import String, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class ChatJob(Base):
    """Job posted in a chat channel for agents to claim and complete.
    
    Jobs are tied to channels and have categories for auto-routing.
    Agents can claim open jobs, work on them in private sub-channels,
    and mark them done with a summary.
    
    Extension Points:
        - Add job priorities (low/medium/high)
        - Add job deadlines
        - Add job dependencies
        - Add payment/reward tracking
    """
    
    __tablename__ = "chat_jobs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    title: Mapped[str] = mapped_column(String, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String, default="general")  # frontend, backend, devops, data, qa, research
    channel: Mapped[str] = mapped_column(String, nullable=False)  # Channel where job was posted
    status: Mapped[str] = mapped_column(String, default="open")  # open, claimed, done
    claimed_by: Mapped[str | None] = mapped_column(String, nullable=True)
    created_by: Mapped[str] = mapped_column(String, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
