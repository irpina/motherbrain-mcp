"""Agent spawn API for launching containerized agents from the UI.

Provides endpoints for managing agent credentials (encrypted API keys)
and spawning/killing agent containers via Docker.
"""
from __future__ import annotations
import os
from datetime import datetime, timezone
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from cryptography.fernet import Fernet
from app.api.deps import require_admin_user
from app.db.session import get_db
from app.models.agent_credential import AgentCredential
from app.models.spawned_agent import SpawnedAgent

router = APIRouter(prefix="/agents", tags=["agent-spawn"])


def _get_fernet() -> Fernet:
    """Get or create Fernet instance for encryption."""
    key = os.getenv("FERNET_KEY")
    if not key:
        # Generate a key for development (not recommended for production)
        key = Fernet.generate_key().decode()
        os.environ["FERNET_KEY"] = key
        print(f"WARNING: Generated FERNET_KEY for development: {key}")
    return Fernet(key.encode())


def _mask_key(key: str) -> str:
    """Mask an API key for display."""
    if len(key) <= 8:
        return "***"
    return key[:4] + "***" + key[-4:]


# ── Credentials Management ───────────────────────────────────────────────────

@router.get("/credentials/")
async def list_credentials(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_admin_user)
):
    """List all agent credentials with masked key status."""
    result = await db.execute(select(AgentCredential))
    creds = result.scalars().all()
    
    return [
        {
            "agent_type": c.agent_type,
            "has_key": True,
            "updated_at": c.updated_at.isoformat()
        }
        for c in creds
    ]


@router.post("/credentials/")
async def store_credential(
    agent_type: str,
    api_key: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_admin_user)
):
    """Store or update an API key for an agent type (encrypted)."""
    fernet = _get_fernet()
    encrypted = fernet.encrypt(api_key.encode())
    
    # Check if credential exists
    result = await db.execute(
        select(AgentCredential).where(AgentCredential.agent_type == agent_type)
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        existing.api_key_encrypted = encrypted
        existing.updated_at = datetime.now(timezone.utc)
    else:
        credential = AgentCredential(
            agent_type=agent_type,
            api_key_encrypted=encrypted
        )
        db.add(credential)
    
    await db.commit()
    
    return {
        "agent_type": agent_type,
        "key_preview": _mask_key(api_key),
        "status": "stored"
    }


@router.delete("/credentials/{agent_type}")
async def delete_credential(
    agent_type: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_admin_user)
):
    """Delete a stored credential."""
    result = await db.execute(
        select(AgentCredential).where(AgentCredential.agent_type == agent_type)
    )
    credential = result.scalar_one_or_none()
    
    if not credential:
        raise HTTPException(status_code=404, detail=f"No credential found for {agent_type}")
    
    await db.delete(credential)
    await db.commit()
    
    return {"agent_type": agent_type, "status": "deleted"}


# ── Spawn Management ─────────────────────────────────────────────────────────

@router.get("/spawnable/")
async def list_spawnable(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_admin_user)
):
    """List available agent types with credential status."""
    # Get stored credentials
    result = await db.execute(select(AgentCredential))
    creds = {c.agent_type: c for c in result.scalars().all()}
    
    # Define available agent types
    agent_types = [
        {"type": "claude", "name": "Claude Code", "description": "Anthropic Claude CLI agent"},
        {"type": "codex", "name": "OpenAI Codex", "description": "OpenAI Codex CLI agent"},
    ]
    
    # Get running counts
    result = await db.execute(
        select(SpawnedAgent).where(SpawnedAgent.status == "running")
    )
    running = {}
    for sa in result.scalars().all():
        running[sa.agent_type] = running.get(sa.agent_type, 0) + 1
    
    return [
        {
            **agent,
            "has_credentials": agent["type"] in creds,
            "running_count": running.get(agent["type"], 0)
        }
        for agent in agent_types
    ]


@router.post("/spawn/")
async def spawn_agent(
    agent_type: str,
    channel: str,
    task: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_admin_user)
):
    """Spawn a new agent container.
    
    Requires:
    - Docker socket mounted at /var/run/docker.sock
    - Credential stored for the agent_type
    """
    # Get and decrypt API key
    result = await db.execute(
        select(AgentCredential).where(AgentCredential.agent_type == agent_type)
    )
    credential = result.scalar_one_or_none()
    
    if not credential:
        raise HTTPException(
            status_code=400,
            detail=f"No credentials stored for {agent_type}. Store credentials first."
        )
    
    fernet = _get_fernet()
    api_key = fernet.decrypt(credential.api_key_encrypted).decode()
    
    # Spawn container via Docker SDK
    try:
        import docker
        client = docker.from_env()
        
        # Determine image and env vars based on agent type
        if agent_type == "claude":
            image = "motherbrain-agent-claude:latest"
            env_key = "ANTHROPIC_API_KEY"
        elif agent_type == "codex":
            image = "motherbrain-agent-codex:latest"
            env_key = "OPENAI_API_KEY"
        else:
            raise HTTPException(status_code=400, detail=f"Unknown agent type: {agent_type}")
        
        # Launch container
        container = client.containers.run(
            image=image,
            detach=True,
            environment={
                env_key: api_key,
                "MCP_SERVER_URL": "http://api:8000/mcp",
                "MCP_API_KEY": os.getenv("API_KEY", "supersecret"),
                "CHANNEL": channel,
                "TASK": task or ""
            },
            network="motherbrain-mcp_default",
            name=f"mb-agent-{agent_type}-{str(uuid4())[:8]}",
            labels={"motherbrain": "spawned-agent", "agent-type": agent_type}
        )
        
        # Record in DB
        spawned = SpawnedAgent(
            agent_type=agent_type,
            container_id=container.id,
            channel=channel,
            task=task
        )
        db.add(spawned)
        await db.commit()
        await db.refresh(spawned)
        
        return {
            "id": spawned.id,
            "agent_type": agent_type,
            "container_id": container.id[:12],
            "channel": channel,
            "status": "running"
        }
        
    except docker.errors.ImageNotFound:
        raise HTTPException(
            status_code=500,
            detail=f"Agent image '{image}' not found. Build it first."
        )
    except docker.errors.APIError as e:
        raise HTTPException(status_code=500, detail=f"Docker error: {e}")


@router.get("/spawned/")
async def list_spawned(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_admin_user)
):
    """List all spawned agent containers."""
    result = await db.execute(
        select(SpawnedAgent).order_by(SpawnedAgent.created_at.desc())
    )
    agents = result.scalars().all()
    
    return [
        {
            "id": a.id,
            "agent_type": a.agent_type,
            "container_id": a.container_id[:12],
            "channel": a.channel,
            "status": a.status,
            "task": a.task,
            "created_at": a.created_at.isoformat()
        }
        for a in agents
    ]


@router.delete("/spawned/{agent_id}")
async def kill_spawned(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_admin_user)
):
    """Kill a spawned agent container."""
    result = await db.execute(
        select(SpawnedAgent).where(SpawnedAgent.id == agent_id)
    )
    spawned = result.scalar_one_or_none()
    
    if not spawned:
        raise HTTPException(status_code=404, detail="Spawned agent not found")
    
    # Kill container
    try:
        import docker
        client = docker.from_env()
        container = client.containers.get(spawned.container_id)
        container.stop(timeout=10)
        container.remove(force=True)
    except docker.errors.NotFound:
        pass  # Already gone
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to kill container: {e}")
    
    # Update DB
    spawned.status = "stopped"
    spawned.stopped_at = datetime.now(timezone.utc)
    await db.commit()
    
    return {"id": agent_id, "status": "stopped"}
