from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.project_context import ProjectContext
from app.schemas.project_context import ProjectContextCreate, ProjectContextUpdate
from app.services.permission_service import check_context_permission
from app.services import user_service


async def create_or_update_context(
    db: AsyncSession, 
    key: str, 
    create: ProjectContextCreate
) -> ProjectContext:
    result = await db.execute(select(ProjectContext).where(ProjectContext.context_key == key))
    context = result.scalar_one_or_none()
    
    if context:
        context.value = create.value
        context.updated_by = create.updated_by
        context.last_updated = datetime.now(timezone.utc)
        if create.description is not None:
            context.description = create.description
        if create.service_id is not None:
            context.service_id = create.service_id
        if create.category is not None:
            context.category = create.category
    else:
        context = ProjectContext(
            context_key=key,
            value=create.value,
            updated_by=create.updated_by,
            description=create.description,
            service_id=create.service_id,
            category=create.category
        )
        db.add(context)
    
    await db.commit()
    await db.refresh(context)
    return context


async def get_context(
    db: AsyncSession, 
    key: str, 
    token: Optional[str] = None
) -> ProjectContext | None:
    """Get a context entry. If token provided, checks RBAC permissions.
    
    Returns None if:
    - Entry doesn't exist
    - Entry exists but user doesn't have permission (to avoid leaking existence)
    """
    result = await db.execute(select(ProjectContext).where(ProjectContext.context_key == key))
    context = result.scalar_one_or_none()
    
    if not context:
        return None
    
    # If no token provided, return the entry (backward compatibility)
    if token is None:
        return context
    
    # Check permission
    allowed, reason = await check_context_permission(db, token, context.service_id)
    if allowed:
        return context
    
    # Return None to avoid leaking existence of restricted skills
    return None


async def get_all_contexts(
    db: AsyncSession,
    token: Optional[str] = None,
    category: Optional[str] = None
) -> list[ProjectContext]:
    """Get all context entries with optional filtering.
    
    If token provided, filters by RBAC permissions.
    Admins see all entries; users see public + permitted service entries.
    """
    # Build base query
    query = select(ProjectContext)
    
    # Apply category filter if provided
    if category:
        query = query.where(ProjectContext.category == category)
    
    query = query.order_by(ProjectContext.context_key)
    result = await db.execute(query)
    contexts = list(result.scalars().all())
    
    # If no token, return all (backward compatibility)
    if token is None:
        return contexts
    
    # Check if user is admin
    user = await user_service.get_user_by_token(db, token)
    if user and user.is_active and user.role == "admin":
        return contexts
    
    # Filter by permission
    permitted_contexts = []
    for ctx in contexts:
        allowed, _ = await check_context_permission(db, token, ctx.service_id)
        if allowed:
            permitted_contexts.append(ctx)
    
    return permitted_contexts


async def delete_context(db: AsyncSession, key: str) -> bool:
    result = await db.execute(select(ProjectContext).where(ProjectContext.context_key == key))
    context = result.scalar_one_or_none()
    if context:
        await db.delete(context)
        await db.commit()
        return True
    return False


async def check_write_permission(
    db: AsyncSession,
    token: str,
    target_service_id: Optional[str]
) -> tuple[bool, str]:
    """Check if user can write a skill with the given service_id restriction.
    
    - If target_service_id is None → any authenticated user can write
    - If target_service_id is set → user must have permission on that service
    """
    user = await user_service.get_user_by_token(db, token)
    if not user:
        return False, "Invalid or expired token"
    if not user.is_active:
        return False, "User account is inactive"
    
    # Admins can write any skill
    if user.role == "admin":
        return True, "admin"
    
    # Public skills can be written by any authenticated user
    if target_service_id is None:
        return True, "public skill"
    
    # For restricted skills, user needs permission on that service
    allowed, reason = await check_context_permission(db, token, target_service_id)
    return allowed, reason
