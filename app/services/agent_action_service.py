from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.agent_action import AgentAction
from app.schemas.agent_action import AgentActionCreate


async def create_action(db: AsyncSession, action_create: AgentActionCreate) -> AgentAction:
    action = AgentAction(
        agent_id=action_create.agent_id,
        action_type=action_create.action_type,
        job_id=action_create.job_id,
        details=action_create.details
    )
    db.add(action)
    await db.commit()
    await db.refresh(action)
    return action


async def get_actions_by_agent(db: AsyncSession, agent_id: str, limit: int = 100) -> list[AgentAction]:
    result = await db.execute(
        select(AgentAction)
        .where(AgentAction.agent_id == agent_id)
        .order_by(AgentAction.timestamp.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_actions_by_job(db: AsyncSession, job_id: str, limit: int = 100) -> list[AgentAction]:
    result = await db.execute(
        select(AgentAction)
        .where(AgentAction.job_id == job_id)
        .order_by(AgentAction.timestamp.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_all_actions(db: AsyncSession, limit: int = 100) -> list[AgentAction]:
    result = await db.execute(
        select(AgentAction)
        .order_by(AgentAction.timestamp.desc())
        .limit(limit)
    )
    return list(result.scalars().all())
