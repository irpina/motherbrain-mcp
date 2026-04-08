"""Group model for RBAC.

Permission groups that define which MCP services users can access.
Users belong to one or more groups.
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4
from sqlalchemy import String, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class Group(Base):
    """Permission group for RBAC.
    
    Attributes:
        group_id: Unique identifier (UUID)
        name: Unique group name
        description: Optional description
        allowed_service_ids: List of MCP service IDs this group can access
        entra_group_id: Microsoft Entra group ID for future SSO integration
        created_at: Group creation timestamp
    """
    __tablename__ = "groups"

    group_id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    allowed_service_ids: Mapped[list] = mapped_column(JSON, default=list)
    entra_group_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
