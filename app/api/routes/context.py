from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import verify_api_key
from app.db.session import get_db
from app.schemas.project_context import ProjectContextCreate, ProjectContextUpdate, ProjectContextResponse
from app.services import project_context_service


router = APIRouter()


@router.get("/", response_model=list[ProjectContextResponse])
async def list_contexts(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key)
):
    """List all project context keys. Admin only."""
    contexts = await project_context_service.get_all_contexts(db)
    return contexts


@router.get("/{key}", response_model=ProjectContextResponse)
async def get_context(
    key: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key)
):
    """Get a context value by key. Admin only."""
    context = await project_context_service.get_context(db, key)
    if not context:
        raise HTTPException(status_code=404, detail="Context key not found")
    return context


@router.post("/{key}", response_model=ProjectContextResponse)
async def set_context(
    key: str,
    create: ProjectContextCreate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key)
):
    """Create or update a context value. Admin only."""
    context = await project_context_service.create_or_update_context(db, key, create)
    return context


@router.put("/{key}", response_model=ProjectContextResponse)
async def update_context(
    key: str,
    update: ProjectContextUpdate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key)
):
    """Update an existing context value. Admin only."""
    create = ProjectContextCreate(
        context_key=key,
        value=update.value,
        updated_by=update.updated_by,
        description=update.description
    )
    context = await project_context_service.create_or_update_context(db, key, create)
    return context


@router.delete("/{key}")
async def delete_context(
    key: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key)
):
    """Delete a context key. Admin only."""
    deleted = await project_context_service.delete_context(db, key)
    if not deleted:
        raise HTTPException(status_code=404, detail="Context key not found")
    return {"status": "ok", "deleted_key": key}
