from __future__ import annotations
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import String, DateTime, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class Rule(Base):
    """Shared working rules for the agent collective.

    Agents propose rules via MCP; humans activate them from the dashboard.
    Only active rules are injected into agent system prompts.

    Status flow:
        pending -> active (human approves)
        pending -> archived (human rejects or agent withdraws)
        active -> archived (human deactivates)
        active -> draft (human edits)
        draft -> active (human re-approves)
    """

    __tablename__ = "rules"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    text: Mapped[str] = mapped_column(String(500), nullable=False)
    author: Mapped[str] = mapped_column(String, nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String, default="pending")  # pending, active, archived, draft
    epoch: Mapped[int] = mapped_column(Integer, default=0)  # bumped when active set changes
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
