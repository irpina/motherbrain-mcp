from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.project_context import ProjectContext
from app.schemas.project_context import ProjectContextCreate, ProjectContextUpdate


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
    else:
        context = ProjectContext(
            context_key=key,
            value=create.value,
            updated_by=create.updated_by,
            description=create.description
        )
        db.add(context)
    
    await db.commit()
    await db.refresh(context)
    return context


async def get_context(db: AsyncSession, key: str) -> ProjectContext | None:
    result = await db.execute(select(ProjectContext).where(ProjectContext.context_key == key))
    return result.scalar_one_or_none()


async def get_all_contexts(db: AsyncSession) -> list[ProjectContext]:
    result = await db.execute(select(ProjectContext).order_by(ProjectContext.context_key))
    return list(result.scalars().all())


async def delete_context(db: AsyncSession, key: str) -> bool:
    result = await db.execute(select(ProjectContext).where(ProjectContext.context_key == key))
    context = result.scalar_one_or_none()
    if context:
        await db.delete(context)
        await db.commit()
        return True
    return False
