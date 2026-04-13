from __future__ import annotations
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class Channel(Base):
    """Chat channel for agent coordination.
    
    Channels are persistent chat rooms where agents and humans can communicate.
    Messages are stored in ChatMessage and broadcast via Redis pub/sub for
    real-time delivery.
    
    Extension Points:
        - Add channel types (public, private, direct)
        - Add channel permissions/ACLs
        - Add channel archiving/retention policies
    """
    
    __tablename__ = "channels"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String, unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
