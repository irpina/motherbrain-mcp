from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import verify_api_key
from app.db.session import get_db
from app.schemas.project_context import ProjectContextCreate, ProjectContextUpdate, ProjectContextResponse
from app.services import project_context_service


router = APIRouter()


def _is_admin_request(request: Request) -> bool:
    """Check if request has admin API key (bypasses user token checks)."""
    api_key = request.headers.get("X-API-Key")
    if api_key:
        from app.core.config import settings
        return api_key == settings.API_KEY
    return False


@router.get("/", response_model=list[ProjectContextResponse])
async def list_contexts(
    request: Request,
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    api_key_user: str = Depends(verify_api_key),
    x_user_token: Optional[str] = Header(None, alias="X-User-Token")
):
    """List all project context entries.
    
    If X-User-Token is provided, filters by RBAC permissions.
    Admins see all entries; regular users see only permitted entries.
    Optional category filter for UI organization.
    """
    # Admins using API key bypass all filtering
    if _is_admin_request(request):
        contexts = await project_context_service.get_all_contexts(db, token=None, category=category)
    else:
        contexts = await project_context_service.get_all_contexts(db, token=x_user_token, category=category)
    return contexts


@router.get("/{key}", response_model=ProjectContextResponse)
async def get_context(
    request: Request,
    key: str,
    db: AsyncSession = Depends(get_db),
    api_key_user: str = Depends(verify_api_key),
    x_user_token: Optional[str] = Header(None, alias="X-User-Token")
):
    """Get a context value by key.
    
    If X-User-Token is provided, checks RBAC permissions.
    Returns 404 if not found or if user doesn't have permission.
    """
    # Admins using API key bypass permission checks
    token = None if _is_admin_request(request) else x_user_token
    context = await project_context_service.get_context(db, key, token=token)
    if not context:
        raise HTTPException(status_code=404, detail="Context key not found")
    return context


@router.post("/{key}", response_model=ProjectContextResponse)
async def set_context(
    request: Request,
    key: str,
    create: ProjectContextCreate,
    db: AsyncSession = Depends(get_db),
    api_key_user: str = Depends(verify_api_key),
    x_user_token: Optional[str] = Header(None, alias="X-User-Token")
):
    """Create or update a context value.
    
    If X-User-Token is provided, checks write permissions for restricted skills.
    Users can only create/update restricted skills if they have permission on the target service.
    """
    # Check write permission if user token provided and setting a restricted skill
    if not _is_admin_request(request) and x_user_token and create.service_id:
        allowed, reason = await project_context_service.check_write_permission(
            db, x_user_token, create.service_id
        )
        if not allowed:
            raise HTTPException(status_code=403, detail=f"Permission denied: {reason}")
    
    context = await project_context_service.create_or_update_context(db, key, create)
    return context


@router.put("/{key}", response_model=ProjectContextResponse)
async def update_context(
    request: Request,
    key: str,
    update: ProjectContextUpdate,
    db: AsyncSession = Depends(get_db),
    api_key_user: str = Depends(verify_api_key),
    x_user_token: Optional[str] = Header(None, alias="X-User-Token")
):
    """Update an existing context value.
    
    If X-User-Token is provided, checks write permissions for restricted skills.
    """
    # Check write permission if user token provided and setting a restricted skill
    if not _is_admin_request(request) and x_user_token and update.service_id:
        allowed, reason = await project_context_service.check_write_permission(
            db, x_user_token, update.service_id
        )
        if not allowed:
            raise HTTPException(status_code=403, detail=f"Permission denied: {reason}")
    
    context = await project_context_service.create_or_update_context(db, key, update)
    return context


@router.delete("/{key}")
async def delete_context(
    key: str,
    db: AsyncSession = Depends(get_db),
    api_key_user: str = Depends(verify_api_key)
):
    """Delete a context key. Admin only."""
    deleted = await project_context_service.delete_context(db, key)
    if not deleted:
        raise HTTPException(status_code=404, detail="Context key not found")
    return {"status": "ok", "deleted_key": key}
