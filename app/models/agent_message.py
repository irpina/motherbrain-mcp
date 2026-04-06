from __future__ import annotations
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import String, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class AgentMessage(Base):
    __tablename__ = "agent_messages"
    
    message_id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    sender_id: Mapped[str] = mapped_column(String)
    recipient_id: Mapped[str] = mapped_column(String)
    content: Mapped[str] = mapped_column(String)
    message_type: Mapped[str] = mapped_column(String, default="text")
    priority: Mapped[str] = mapped_column(String, default="normal")
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    delivered: Mapped[bool] = mapped_column(Boolean, default=False)
    read: Mapped[bool] = mapped_column(Boolean, default=False)
