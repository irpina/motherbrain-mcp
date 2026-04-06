from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import verify_api_key
from app.db.session import get_db
from app.schemas.agent_action import AgentActionResponse
from app.services import agent_action_service


router = APIRouter()


@router.get("/", response_model=list[AgentActionResponse])
async def list_actions(
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key)
):
    """List all agent actions (audit log). Admin only."""
    actions = await agent_action_service.get_all_actions(db, limit)
    return actions


@router.get("/agent/{agent_id}", response_model=list[AgentActionResponse])
async def get_agent_actions(
    agent_id: str,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key)
):
    """Get actions for a specific agent. Admin only."""
    actions = await agent_action_service.get_actions_by_agent(db, agent_id, limit)
    return actions


@router.get("/job/{job_id}", response_model=list[AgentActionResponse])
async def get_job_actions(
    job_id: str,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key)
):
    """Get actions related to a specific job. Admin only."""
    actions = await agent_action_service.get_actions_by_job(db, job_id, limit)
    return actions
