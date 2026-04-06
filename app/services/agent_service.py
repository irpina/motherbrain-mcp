"""Agent Service — Business logic for agent management.

This module handles agent registration, authentication, heartbeat tracking,
and status management.

Extension Points:
    - Add agent performance metrics tracking
    - Add agent grouping/roles for access control
    - Add agent resource limits (max concurrent jobs)
"""

from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.agent import Agent
from app.schemas.agent import AgentCreate


async def register_agent(db: AsyncSession, agent_create: AgentCreate) -> Agent:
    """Register a new agent and return it with its authentication token.
    
    The token is generated server-side and must be saved by the agent.
    It cannot be retrieved later - if lost, the agent must re-register.
    """

    agent = Agent(
        platform=agent_create.platform,
        capabilities=agent_create.capabilities,
        token=str(uuid4())  # Generate unique token on registration
    )
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    return agent


async def update_heartbeat(db: AsyncSession, agent_id: str) -> Agent:
    result = await db.execute(select(Agent).where(Agent.agent_id == agent_id))
    agent = result.scalar_one_or_none()
    if agent:
        agent.last_heartbeat = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(agent)
    return agent


async def list_agents(db: AsyncSession) -> list[Agent]:
    result = await db.execute(select(Agent))
    return list(result.scalars().all())


async def get_agent(db: AsyncSession, agent_id: str) -> Agent | None:
    result = await db.execute(select(Agent).where(Agent.agent_id == agent_id))
    return result.scalar_one_or_none()


async def get_agent_by_token(db: AsyncSession, token: str) -> Agent | None:
    """Get agent by its authentication token."""
    result = await db.execute(select(Agent).where(Agent.token == token))
    return result.scalar_one_or_none()


async def update_agent_status(db: AsyncSession, agent_id: str, status: str) -> Agent | None:
    """Update agent status (online, offline, busy, etc)."""
    result = await db.execute(select(Agent).where(Agent.agent_id == agent_id))
    agent = result.scalar_one_or_none()
    if agent:
        agent.status = status
        await db.commit()
        await db.refresh(agent)
    return agent
