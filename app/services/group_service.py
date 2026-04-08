"""Group Service — Business logic for permission group management.

Handles group CRUD and service permission assignment.
"""
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.group import Group
from app.schemas.group import GroupCreate, GroupUpdate


async def create_group(db: AsyncSession, data: GroupCreate) -> Group:
    """Create a new permission group."""
    group = Group(
        group_id=str(uuid4()),
        name=data.name,
        description=data.description,
        allowed_service_ids=data.allowed_service_ids or [],
    )
    
    db.add(group)
    await db.commit()
    await db.refresh(group)
    return group


async def get_group(db: AsyncSession, group_id: str) -> Group | None:
    """Get a group by ID."""
    result = await db.execute(select(Group).where(Group.group_id == group_id))
    return result.scalar_one_or_none()


async def get_group_by_name(db: AsyncSession, name: str) -> Group | None:
    """Get a group by name."""
    result = await db.execute(select(Group).where(Group.name == name))
    return result.scalar_one_or_none()


async def list_groups(db: AsyncSession) -> list[Group]:
    """List all groups."""
    result = await db.execute(select(Group))
    return list(result.scalars().all())


async def update_group(db: AsyncSession, group_id: str, data: GroupUpdate) -> Group | None:
    """Update group properties."""
    group = await get_group(db, group_id)
    if not group:
        return None
    
    if data.name is not None:
        group.name = data.name
    if data.description is not None:
        group.description = data.description
    if data.allowed_service_ids is not None:
        group.allowed_service_ids = data.allowed_service_ids
    
    await db.commit()
    await db.refresh(group)
    return group


async def delete_group(db: AsyncSession, group_id: str) -> bool:
    """Delete a group.
    
    Returns True if group was found and deleted.
    Note: UserGroup junction entries are deleted via CASCADE.
    """
    group = await get_group(db, group_id)
    if not group:
        return False
    
    await db.delete(group)
    await db.commit()
    return True
