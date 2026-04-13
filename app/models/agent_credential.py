from __future__ import annotations
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import String, DateTime, LargeBinary
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class AgentCredential(Base):
    """Encrypted API credentials for spawning agents.
    
    Stores API keys (e.g., ANTHROPIC_API_KEY, OPENAI_API_KEY) encrypted at rest
    using Fernet symmetric encryption. The encryption key is stored in the
    FERNET_KEY environment variable.
    
    Extension Points:
        - Add OAuth token support (refresh tokens)
        - Add credential rotation/expiration
        - Add per-credential usage quotas
    """
    
    __tablename__ = "agent_credentials"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    agent_type: Mapped[str] = mapped_column(String, unique=True, index=True)  # claude, codex, gemini
    api_key_encrypted: Mapped[bytes] = mapped_column(LargeBinary)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
