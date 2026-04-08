"""User Service — Business logic for user management and RBAC.

Handles user creation, authentication, group membership, and token management.
"""
import hashlib
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.group import Group
from app.models.user_group import UserGroup
from app.schemas.user import UserCreate, UserUpdate


def _hash_token(token: str) -> str:
    """Hash a token using SHA-256."""
    return hashlib.sha256(token.encode()).hexdigest()


async def create_user(db: AsyncSession, data: UserCreate) -> tuple[User, str]:
    """Create a new user and return the user with its plaintext token.
    
    The token is generated server-side and returned as plaintext ONCE.
    Only the hash is stored in the database. If the token is lost,
    the user must be re-created.
    
    Returns:
        Tuple of (User, plaintext_token)
    """
    # Generate token with mb_ prefix for identification
    plaintext_token = f"mb_{uuid4().hex}"
    
    user = User(
        user_id=str(uuid4()),
        name=data.name,
        email=data.email,
        role=data.role,
        token_hash=_hash_token(plaintext_token),
        is_active=True,
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user, plaintext_token


async def get_user(db: AsyncSession, user_id: str) -> User | None:
    """Get a user by ID."""
    result = await db.execute(select(User).where(User.user_id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_token(db: AsyncSession, token: str) -> User | None:
    """Get a user by their authentication token.
    
    The input token is hashed and compared against stored token_hash.
    Only returns active users.
    """
    hashed = _hash_token(token)
    result = await db.execute(
        select(User).where(User.token_hash == hashed, User.is_active == True)
    )
    return result.scalar_one_or_none()


async def list_users(db: AsyncSession) -> list[User]:
    """List all users."""
    result = await db.execute(select(User))
    return list(result.scalars().all())


async def update_user(db: AsyncSession, user_id: str, data: UserUpdate) -> User | None:
    """Update user properties."""
    user = await get_user(db, user_id)
    if not user:
        return None
    
    if data.name is not None:
        user.name = data.name
    if data.email is not None:
        user.email = data.email
    if data.role is not None:
        user.role = data.role
    if data.is_active is not None:
        user.is_active = data.is_active
    
    await db.commit()
    await db.refresh(user)
    return user


async def deactivate_user(db: AsyncSession, user_id: str) -> bool:
    """Deactivate a user (soft delete).
    
    Returns True if user was found and deactivated.
    """
    user = await get_user(db, user_id)
    if not user:
        return False
    
    user.is_active = False
    await db.commit()
    return True


async def add_user_to_group(db: AsyncSession, user_id: str, group_id: str) -> bool:
    """Add a user to a group.
    
    Returns True if added, False if user or group not found.
    """
    # Verify user exists
    user = await get_user(db, user_id)
    if not user:
        return False
    
    # Verify group exists
    from app.services.group_service import get_group
    group = await get_group(db, group_id)
    if not group:
        return False
    
    # Check if already in group
    result = await db.execute(
        select(UserGroup).where(
            UserGroup.user_id == user_id,
            UserGroup.group_id == group_id
        )
    )
    if result.scalar_one_or_none():
        return True  # Already in group
    
    # Add to group
    user_group = UserGroup(user_id=user_id, group_id=group_id)
    db.add(user_group)
    await db.commit()
    return True


async def remove_user_from_group(db: AsyncSession, user_id: str, group_id: str) -> bool:
    """Remove a user from a group.
    
    Returns True if removed, False if membership not found.
    """
    result = await db.execute(
        select(UserGroup).where(
            UserGroup.user_id == user_id,
            UserGroup.group_id == group_id
        )
    )
    user_group = result.scalar_one_or_none()
    if not user_group:
        return False
    
    await db.delete(user_group)
    await db.commit()
    return True


async def get_user_groups(db: AsyncSession, user_id: str) -> list[Group]:
    """Get all groups a user belongs to."""
    result = await db.execute(
        select(Group)
        .join(UserGroup, Group.group_id == UserGroup.group_id)
        .where(UserGroup.user_id == user_id)
    )
    return list(result.scalars().all())


async def regenerate_token(db: AsyncSession, user_id: str) -> str | None:
    """Generate a new token for a user.
    
    Returns the new plaintext token, or None if user not found.
    """
    user = await get_user(db, user_id)
    if not user:
        return None
    
    plaintext_token = f"mb_{uuid4().hex}"
    user.token_hash = _hash_token(plaintext_token)
    await db.commit()
    return plaintext_token
