"""UserGroup junction model for RBAC.

Many-to-many relationship between users and groups.
"""
from __future__ import annotations
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class UserGroup(Base):
    """Junction table linking users to their permission groups.
    
    Attributes:
        user_id: FK to users.user_id
        group_id: FK to groups.group_id
    """
    __tablename__ = "user_groups"

    user_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        primary_key=True
    )
    group_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("groups.group_id", ondelete="CASCADE"),
        primary_key=True
    )
