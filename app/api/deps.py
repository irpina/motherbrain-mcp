from typing import Optional
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


async def require_admin_user(
    x_api_key: Optional[str] = Header(None),
    x_user_token: Optional[str] = Header(None, alias="X-User-Token"),
    db: AsyncSession = Depends(get_db)
):
    """Require admin access via API key OR RBAC admin user token.
    
    This allows either:
    - Master API key (for services/scripts)
    - X-User-Token with role="admin" (for dashboard/admin users)
    
    Args:
        x_api_key: Master API key header
        x_user_token: User authentication token (from RBAC system)
        db: Database session
    
    Raises:
        HTTPException: 403 if neither valid API key nor admin user token provided
    """
    # Path 1: Master API key (backward compat for services)
    if x_api_key and x_api_key == settings.API_KEY:
        return
    
    # Path 2: RBAC admin user token
    if x_user_token:
        from app.services.user_service import get_user_by_token
        user = await get_user_by_token(db, x_user_token)
        if user and user.is_active and user.role == "admin":
            return
    
    raise HTTPException(status_code=403, detail="Admin access required")
