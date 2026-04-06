from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import verify_api_key, get_current_agent
from app.db.session import get_db
from app.schemas.agent_message import AgentMessageCreate, AgentMessageResponse, AgentMessageUpdate
from app.services import agent_message_service


router = APIRouter()


@router.post("/", response_model=AgentMessageResponse)
async def send_message(
    message_create: AgentMessageCreate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key)
):
    """Send a message from one agent to another. Admin only."""
    message = await agent_message_service.create_message(db, message_create)
    return message


@router.get("/inbox", response_model=list[AgentMessageResponse])
async def get_inbox(
    unread_only: bool = False,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    agent = Depends(get_current_agent)
):
    """Get messages for the authenticated agent. Requires agent token."""
    messages = await agent_message_service.get_messages_for_recipient(
        db, agent.agent_id, unread_only, limit
    )
    # Mark as delivered
    await agent_message_service.mark_all_delivered(db, agent.agent_id)
    return messages


@router.get("/sent", response_model=list[AgentMessageResponse])
async def get_sent_messages(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    agent = Depends(get_current_agent)
):
    """Get messages sent by the authenticated agent. Requires agent token."""
    messages = await agent_message_service.get_messages_from_sender(db, agent.agent_id, limit)
    return messages


@router.get("/{message_id}", response_model=AgentMessageResponse)
async def get_message(
    message_id: str,
    db: AsyncSession = Depends(get_db),
    agent = Depends(get_current_agent)
):
    """Get a specific message. Requires agent token and agent must be sender or recipient."""
    message = await agent_message_service.get_message(db, message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Verify agent is sender or recipient
    if message.sender_id != agent.agent_id and message.recipient_id != agent.agent_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this message")
    
    return message


@router.post("/{message_id}/read")
async def mark_message_read(
    message_id: str,
    db: AsyncSession = Depends(get_db),
    agent = Depends(get_current_agent)
):
    """Mark a message as read. Requires agent token and agent must be recipient."""
    message = await agent_message_service.get_message(db, message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    if message.recipient_id != agent.agent_id:
        raise HTTPException(status_code=403, detail="Only the recipient can mark as read")
    
    update = AgentMessageUpdate(delivered=True, read=True)
    updated = await agent_message_service.update_message(db, message_id, update)
    return {"status": "ok", "message_id": message_id}
