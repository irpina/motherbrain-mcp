from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.db.session import get_db
from app.services.agent_service import get_agent_by_token


async def verify_api_key(x_api_key: str = Header(...)):
    """Verify the master API key for admin-level access."""
    if x_api_key != settings.API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")


async def get_current_agent(
    x_agent_token: str = Header(...),
    db: AsyncSession = Depends(get_db)
):
    """Verify agent token and return the agent. Used for agent-level routes."""
    agent = await get_agent_by_token(db, x_agent_token)
    if not agent:
        raise HTTPException(status_code=401, detail="Invalid agent token")
    return agent
