"""Permission Service — RBAC permission checking.

Verifies if a user (identified by token) has access to a specific MCP service.
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.services import user_service


async def check_permission(db: AsyncSession, token: str, service_id: str) -> tuple[bool, str]:
    """Check if a user has permission to access a service.
    
    Args:
        db: Database session
        token: The user's authentication token
        service_id: The MCP service ID to check access for
    
    Returns:
        Tuple of (allowed: bool, reason: str)
        - allowed: True if user can access the service
        - reason: Explanation for debugging/denial messages
                  "admin" | "permitted via group 'X'" | "No permission..." | etc.
    """
    # Get user by token
    user = await user_service.get_user_by_token(db, token)
    if not user:
        return False, "Invalid or expired token"
    
    if not user.is_active:
        return False, "User account is inactive"
    
    # Admins bypass all restrictions
    if user.role == "admin":
        return True, "admin"
    
    # Check group permissions
    groups = await user_service.get_user_groups(db, user.user_id)
    
    for group in groups:
        allowed_services = group.allowed_service_ids or []
        if service_id in allowed_services:
            return True, f"permitted via group '{group.name}'"
    
    return False, f"No permission to access service '{service_id}'"


async def get_permitted_services(db: AsyncSession, token: str) -> list[str]:
    """Get list of services a user is permitted to access.
    
    Args:
        db: Database session
        token: The user's authentication token
    
    Returns:
        List of service IDs the user can access.
        Admins get empty list (they can access all).
    """
    user = await user_service.get_user_by_token(db, token)
    if not user:
        return []
    
    if not user.is_active:
        return []
    
    if user.role == "admin":
        return []  # Admins can access all, caller should check role
    
    # Collect all unique service IDs from user's groups
    groups = await user_service.get_user_groups(db, user.user_id)
    permitted = set()
    
    for group in groups:
        permitted.update(group.allowed_service_ids or [])
    
    return list(permitted)


async def check_context_permission(db: AsyncSession, token: str, context_service_id: Optional[str]) -> tuple[bool, str]:
    """Check if a user can access a context/skill entry.
    
    - If context_service_id is None → allowed for all authenticated users
    - If context_service_id is set → delegate to check_permission(token, context_service_id)
    
    Args:
        db: Database session
        token: The user's authentication token
        context_service_id: The service_id associated with the context entry (None = public)
    
    Returns:
        Tuple of (allowed: bool, reason: str)
    """
    if context_service_id is None:
        # Public skill - any authenticated user can access
        user = await user_service.get_user_by_token(db, token)
        if not user:
            return False, "Invalid or expired token"
        if not user.is_active:
            return False, "User account is inactive"
        return True, "public skill"
    
    # Restricted skill - use standard permission check
    return await check_permission(db, token, context_service_id)
