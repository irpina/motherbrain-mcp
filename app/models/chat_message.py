from __future__ import annotations
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import String, DateTime, Text, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class ChatMessage(Base):
    """Chat message in a channel.
    
    Messages are persisted to PostgreSQL and broadcast via Redis pub/sub
    for real-time WebSocket delivery. The id is an auto-incrementing integer
    for efficient cursor-based pagination (since_id).
    
    Extension Points:
        - Add message reactions/emoji
        - Add message threading (parent_message_id)
        - Add message edits/history
        - Add file attachments
    """
    
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    channel_id: Mapped[str] = mapped_column(String, ForeignKey("channels.id", ondelete="CASCADE"), index=True)
    sender: Mapped[str] = mapped_column(String, index=True)  # Agent name or "user:{username}"
    text: Mapped[str] = mapped_column(Text)
    type: Mapped[str] = mapped_column(String, default="chat")  # chat, system, join, leave
    reply_to: Mapped[int | None] = mapped_column(Integer, ForeignKey("chat_messages.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
