"""Group schemas for RBAC.
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class GroupCreate(BaseModel):
    """Schema for creating a new group."""
    name: str
    description: Optional[str] = None
    allowed_service_ids: list[str] = []


class GroupUpdate(BaseModel):
    """Schema for updating a group."""
    name: Optional[str] = None
    description: Optional[str] = None
    allowed_service_ids: Optional[list[str]] = None


class GroupResponse(BaseModel):
    """Schema for group response."""
    group_id: str
    name: str
    description: Optional[str]
    allowed_service_ids: list[str]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
