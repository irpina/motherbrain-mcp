"""Admin routes for RBAC user and group management.

All endpoints require the admin API key (X-API-Key header).
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import verify_api_key
from app.db.session import get_db
from app.schemas.user import UserCreate, UserResponse, UserRegistrationResponse, UserUpdate
from app.schemas.group import GroupCreate, GroupUpdate, GroupResponse
from app.services import user_service, group_service


router = APIRouter(prefix="/admin", tags=["admin"])


# ========== Users ==========

@router.post("/users", response_model=UserRegistrationResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key)
):
    """Create a new user. Returns the user with a one-time token."""
    # Check if email already exists
    if data.email:
        existing = await user_service.get_user_by_email(db, data.email)
        if existing:
            raise HTTPException(status_code=409, detail="Email already registered")
    
    user, token = await user_service.create_user(db, data)
    return UserRegistrationResponse(
        user_id=user.user_id,
        name=user.name,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
        token=token
    )


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key)
):
    """List all users."""
    users = await user_service.list_users(db)
    return users


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key)
):
    """Get a specific user by ID."""
    user = await user_service.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key)
):
    """Update a user."""
    user = await user_service.update_user(db, user_id, data)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.delete("/users/{user_id}")
async def deactivate_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key)
):
    """Deactivate a user (soft delete)."""
    deactivated = await user_service.deactivate_user(db, user_id)
    if not deactivated:
        raise HTTPException(status_code=404, detail="User not found")
    return {"status": "ok", "user_id": user_id}


@router.post("/users/{user_id}/groups/{group_id}")
async def add_user_to_group(
    user_id: str,
    group_id: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key)
):
    """Add a user to a group."""
    added = await user_service.add_user_to_group(db, user_id, group_id)
    if not added:
        raise HTTPException(status_code=404, detail="User or group not found")
    return {"status": "ok", "user_id": user_id, "group_id": group_id}


@router.delete("/users/{user_id}/groups/{group_id}")
async def remove_user_from_group(
    user_id: str,
    group_id: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key)
):
    """Remove a user from a group."""
    removed = await user_service.remove_user_from_group(db, user_id, group_id)
    if not removed:
        raise HTTPException(status_code=404, detail="User not in group")
    return {"status": "ok", "user_id": user_id, "group_id": group_id}


@router.get("/users/{user_id}/groups", response_model=list[GroupResponse])
async def get_user_groups(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key)
):
    """Get all groups a user belongs to."""
    user = await user_service.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    groups = await user_service.get_user_groups(db, user_id)
    return groups


# ========== Groups ==========

@router.post("/groups", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    data: GroupCreate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key)
):
    """Create a new permission group."""
    # Check if name already exists
    existing = await group_service.get_group_by_name(db, data.name)
    if existing:
        raise HTTPException(status_code=409, detail="Group name already exists")
    
    group = await group_service.create_group(db, data)
    return group


@router.get("/groups", response_model=list[GroupResponse])
async def list_groups(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key)
):
    """List all groups."""
    groups = await group_service.list_groups(db)
    return groups


@router.get("/groups/{group_id}", response_model=GroupResponse)
async def get_group(
    group_id: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key)
):
    """Get a specific group by ID."""
    group = await group_service.get_group(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return group


@router.patch("/groups/{group_id}", response_model=GroupResponse)
async def update_group(
    group_id: str,
    data: GroupUpdate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key)
):
    """Update a group (including allowed_service_ids)."""
    group = await group_service.update_group(db, group_id, data)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return group


@router.delete("/groups/{group_id}")
async def delete_group(
    group_id: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key)
):
    """Delete a group."""
    deleted = await group_service.delete_group(db, group_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Group not found")
    return {"status": "ok", "group_id": group_id}
