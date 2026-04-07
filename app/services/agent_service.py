"""Agent Service — Business logic for agent management.

This module handles agent registration, authentication, heartbeat tracking,
and status management.

Extension Points:
    - Add agent performance metrics tracking
    - Add agent grouping/roles for access control
    - Add agent resource limits (max concurrent jobs)
"""

import hashlib
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.agent import Agent
from app.schemas.agent import AgentCreate


def _hash_token(token: str) -> str:
    """Hash a token using SHA-256.
    
    Tokens are UUID4 (122 bits of randomness), so SHA-256 is sufficient
    for secure storage while allowing efficient DB lookup.
    """
    return hashlib.sha256(token.encode()).hexdigest()


async def register_agent(db: AsyncSession, agent_create: AgentCreate) -> tuple[Agent, str]:
    """Register a new agent and return it with its authentication token.
    
    If a name and hostname are provided and an agent with that combination
    already exists, this performs a re-registration: the existing agent is
    updated with new capabilities and a new token, preserving its identity.
    
    If only name is provided (no hostname), always creates a new agent.
    This handles anonymous sessions where hostname is not available.
    
    The token is generated server-side and returned as plaintext ONCE.
    Only the hash is stored in the database. If the token is lost,
    the agent must re-register.
    
    Returns:
        Tuple of (Agent, plaintext_token)
    """
    # Idempotent: match on name+hostname pair if both provided
    if agent_create.name and agent_create.hostname:
        result = await db.execute(
            select(Agent).where(
                Agent.name == agent_create.name,
                Agent.hostname == agent_create.hostname
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            # Re-registration: issue new token, preserve identity
            plaintext_token = str(uuid4())
            existing.token_hash = _hash_token(plaintext_token)
            existing.platform = agent_create.platform
            existing.capabilities = agent_create.capabilities
            existing.last_heartbeat = datetime.now(timezone.utc)
            await db.commit()
            await db.refresh(existing)
            return existing, plaintext_token

    # New agent registration
    plaintext_token = str(uuid4())
    agent = Agent(
        name=agent_create.name or None,
        hostname=agent_create.hostname or None,
        platform=agent_create.platform,
        capabilities=agent_create.capabilities,
        token_hash=_hash_token(plaintext_token)
    )
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    return agent, plaintext_token


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


async def get_agent_by_name(db: AsyncSession, name: str) -> Agent | None:
    """Get agent by its name.
    
    Returns first match. Use get_agent_by_name_and_hostname
    for precise lookup when hostname is known.
    """
    result = await db.execute(select(Agent).where(Agent.name == name))
    return result.scalar_one_or_none()


async def get_agent_by_name_and_hostname(db: AsyncSession, name: str, hostname: str) -> Agent | None:
    """Get agent by its name and hostname combination.
    
    This allows agents to check if they already exist on a specific
    machine without needing their token.
    """
    result = await db.execute(
        select(Agent).where(
            Agent.name == name,
            Agent.hostname == hostname
        )
    )
    return result.scalar_one_or_none()


async def get_agent_by_token(db: AsyncSession, token: str) -> Agent | None:
    """Get agent by its authentication token.
    
    The input token is hashed and compared against stored token_hash.
    """
    hashed = _hash_token(token)
    result = await db.execute(select(Agent).where(Agent.token_hash == hashed))
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
