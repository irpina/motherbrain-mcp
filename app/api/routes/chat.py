"""Chat API routes for real-time agent coordination.

Provides REST endpoints for channel management and message history,
plus WebSocket support for real-time message delivery via Redis pub/sub.
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from typing import AsyncGenerator
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import require_admin_user, get_current_agent
from app.db.session import get_db
from app.models.channel import Channel
from app.models.chat_message import ChatMessage
from app.queue.redis_queue import redis_async

router = APIRouter(prefix="/chat", tags=["chat"])


# ── Channel Management ───────────────────────────────────────────────────────

@router.get("/channels/")
async def list_channels(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_admin_user)
):
    """List all chat channels."""
    result = await db.execute(select(Channel).order_by(Channel.created_at.desc()))
    channels = result.scalars().all()
    return [
        {"id": c.id, "name": c.name, "created_at": c.created_at.isoformat()}
        for c in channels
    ]


@router.post("/channels/")
async def create_channel(
    name: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_admin_user)
):
    """Create a new chat channel."""
    # Check if channel already exists
    result = await db.execute(select(Channel).where(Channel.name == name))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"Channel '{name}' already exists")
    
    channel = Channel(name=name)
    db.add(channel)
    await db.commit()
    await db.refresh(channel)
    
    return {"id": channel.id, "name": channel.name, "created_at": channel.created_at.isoformat()}


# ── Message Management ───────────────────────────────────────────────────────

@router.get("/channels/{channel_name}/messages/")
async def get_messages(
    channel_name: str,
    limit: int = Query(50, ge=1, le=100),
    before_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_admin_user)
):
    """Get messages from a channel with cursor-based pagination."""
    # Get channel
    result = await db.execute(select(Channel).where(Channel.name == channel_name))
    channel = result.scalar_one_or_none()
    if not channel:
        raise HTTPException(status_code=404, detail=f"Channel '{channel_name}' not found")
    
    # Build query
    query = select(ChatMessage).where(ChatMessage.channel_id == channel.id)
    if before_id:
        query = query.where(ChatMessage.id < before_id)
    query = query.order_by(desc(ChatMessage.id)).limit(limit)
    
    result = await db.execute(query)
    messages = result.scalars().all()
    
    return {
        "messages": [
            {
                "id": m.id,
                "sender": m.sender,
                "text": m.text,
                "type": m.type,
                "reply_to": m.reply_to,
                "created_at": m.created_at.isoformat()
            }
            for m in reversed(messages)  # Return oldest first
        ],
        "channel": channel_name
    }


@router.post("/channels/{channel_name}/messages/")
async def post_message(
    channel_name: str,
    sender: str,
    text: str,
    msg_type: str = "chat",
    reply_to: int | None = None,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_admin_user)
):
    """Post a message to a channel (admin API)."""
    return await _save_and_broadcast_message(
        db, channel_name, sender, text, msg_type, reply_to
    )


async def _save_and_broadcast_message(
    db: AsyncSession,
    channel_name: str,
    sender: str,
    text: str,
    msg_type: str = "chat",
    reply_to: int | None = None
) -> dict:
    """Save message to DB and broadcast via Redis."""
    # Get channel
    result = await db.execute(select(Channel).where(Channel.name == channel_name))
    channel = result.scalar_one_or_none()
    if not channel:
        raise HTTPException(status_code=404, detail=f"Channel '{channel_name}' not found")
    
    # Create message
    message = ChatMessage(
        channel_id=channel.id,
        sender=sender,
        text=text,
        type=msg_type,
        reply_to=reply_to
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    
    # Broadcast via Redis pub/sub
    msg_data = {
        "id": message.id,
        "sender": message.sender,
        "text": message.text,
        "type": message.type,
        "reply_to": message.reply_to,
        "created_at": message.created_at.isoformat(),
        "channel": channel_name
    }
    await redis_async.publish(f"chat:{channel_name}", json.dumps(msg_data))
    
    return msg_data


# ── WebSocket Real-time ──────────────────────────────────────────────────────

@router.websocket("/ws/channels/{channel_name}")
async def chat_websocket(
    websocket: WebSocket,
    channel_name: str,
    api_key: str | None = None
):
    """WebSocket endpoint for real-time chat.
    
    Clients connect with: ws://host/chat/ws/channels/{name}?api_key=...
    """
    # TODO: Validate API key here
    # For now, accept all connections (auth middleware should handle this)
    
    await websocket.accept()
    
    # Subscribe to Redis channel
    pubsub = redis_async.pubsub()
    await pubsub.subscribe(f"chat:{channel_name}")
    
    try:
        # Listen for messages from Redis and forward to WebSocket
        async for message in pubsub.listen():
            if message["type"] == "message":
                data = json.loads(message["data"])
                await websocket.send_json(data)
    except WebSocketDisconnect:
        pass
    finally:
        await pubsub.unsubscribe(f"chat:{channel_name}")
