"""User model for RBAC.

Represents a human user of the system with authentication token and role.
Users belong to groups which define their service permissions.
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4
from sqlalchemy import String, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class User(Base):
    """User account for RBAC.
    
    Attributes:
        user_id: Unique identifier (UUID)
        name: Display name
        email: Optional email address (unique)
        role: 'admin' or 'user' — admins bypass all permission checks
        token_hash: SHA-256 hash of the user's API token
        is_active: Whether the account is enabled
        entra_object_id: Microsoft Entra ID for future SSO integration
        created_at: Account creation timestamp
    """
    __tablename__ = "users"

    user_id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String, unique=True, nullable=True)
    role: Mapped[str] = mapped_column(String, nullable=False, default="user")
    token_hash: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    entra_object_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
