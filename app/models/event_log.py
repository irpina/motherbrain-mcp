"""Event Log Model — Database-backed Kafka-style append-only log.

This model stores every MCP tool call event proxied through Motherbrain,
replacing the previous in-memory implementation for persistence across
restarts.
"""

from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional, Any
from uuid import uuid4
from sqlalchemy import String, JSON, DateTime, BigInteger
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class EventLog(Base):
    """Event log entry for MCP tool calls and system events.
    
    Each record represents a single tool invocation with full context
    for debugging and audit purposes.
    
    Extension Points:
        - Add agent_id field to track which agent made the call
        - Add request_id for distributed tracing
        - Add indexing on topic/service_id for query performance
    """
    
    # TODO: Add request_id for distributed tracing
    __tablename__ = "event_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(String, unique=True, default=lambda: str(uuid4()))
    topic: Mapped[str] = mapped_column(String)
    service_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    agent_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    tool_name: Mapped[str] = mapped_column(String)
    arguments: Mapped[dict] = mapped_column(JSON)
    response: Mapped[Any] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String)  # "ok" | "error"
    duration_ms: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
