"""System API Routes — LLM-facing endpoints for system visibility.

These endpoints provide the LLM with situational awareness of the
Motherbrain system — what's available, what's happening, what needs
done. The LLM queries these to decide what actions to take.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import verify_api_key
from app.db.session import get_db
from app.services.system_state import get_system_state


router = APIRouter(tags=["system"])


@router.get("/system/state")
async def get_system_state_endpoint(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key)
):
    """Get comprehensive system state for LLM situational awareness.
    
    Returns everything the LLM needs to understand the current state:
    - MCP services: what's registered and online
    - Agents: who's available to work
    - Jobs: what's pending or running
    - Recent activity: what just happened
    
    This is the primary endpoint for the LLM to query before deciding
    what action to take. One call gets full context.
    
    Example response:
    ```json
    {
      "timestamp": "2026-04-06T18:30:00Z",
      "mcp_services": {
        "count": 2,
        "online": 1,
        "services": [
          {
            "service_id": "agentchattr-mcp",
            "name": "Agent Chattr",
            "status": "online",
            "protocol": "mcp",
            "capabilities": ["chat_send", "chat_read", "chat_who"]
          }
        ]
      },
      "agents": {
        "count": 3,
        "online": 2,
        "agents": [...]
      },
      "jobs": {
        "pending": 5,
        "running": 2,
        "jobs": [...]
      },
      "recent_activity": {
        "action_count": 20,
        "actions": [...]
      }
    }
    ```
    """
    return await get_system_state(db)
