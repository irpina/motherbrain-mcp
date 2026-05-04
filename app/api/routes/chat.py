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
from app.models.chat_job import ChatJob
from app.queue.redis_queue import redis_async, set_key, get_key, delete_key

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
    reply_to: int | None = None,
    hop: int = 0
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
        reply_to=reply_to,
        hop=hop
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
        "hop": hop,
        "created_at": message.created_at.isoformat(),
        "channel": channel_name
    }
    await redis_async.publish(f"chat:{channel_name}", json.dumps(msg_data))
    
    return msg_data


# ── WebSocket Auth Token ─────────────────────────────────────────────────────

@router.post("/ws-token/")
async def create_ws_token(
    _: str = Depends(require_admin_user)
):
    """Issue a short-lived WebSocket auth token (60s, single-use).

    Browser fetches this via the HTTPS proxy, then connects the WebSocket
    directly to port 8000 using the token as a query param.
    """
    import secrets
    token = secrets.token_hex(16)
    await set_key(f"ws_token:{token}", "1", ttl=60)
    return {"token": token, "expires_in": 60}


# ── WebSocket Real-time ──────────────────────────────────────────────────────

@router.websocket("/ws/channels/{channel_name}")
async def chat_websocket(
    websocket: WebSocket,
    channel_name: str,
    token: str | None = None
):
    """Real-time chat via WebSocket.

    Connect to: ws://host:8000/chat/ws/channels/{name}?token=<ws_token>
    Obtain token via POST /chat/ws-token/ (requires X-API-Key header).
    Token is single-use and expires in 60 seconds.
    """
    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return
    key = f"ws_token:{token}"
    valid = await get_key(key)
    if not valid:
        await websocket.close(code=4001, reason="Invalid or expired token")
        return
    await delete_key(key)  # single-use

    await websocket.accept()

    pubsub = redis_async.pubsub()
    await pubsub.subscribe(f"chat:{channel_name}")

    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                data = json.loads(message["data"])
                await websocket.send_json(data)
    except WebSocketDisconnect:
        pass
    finally:
        await pubsub.unsubscribe(f"chat:{channel_name}")


# ── Job Management ───────────────────────────────────────────────────────────

@router.get("/jobs/")
async def list_jobs(
    category: str | None = None,
    status: str = "open",
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_admin_user)
):
    """List jobs with optional filtering."""
    from app.models.chat_job import ChatJob
    
    query = select(ChatJob)
    if category:
        query = query.where(ChatJob.category == category)
    if status:
        query = query.where(ChatJob.status == status)
    query = query.order_by(desc(ChatJob.created_at)).limit(limit)
    
    result = await db.execute(query)
    jobs = result.scalars().all()
    
    return {
        "count": len(jobs),
        "filters": {"category": category, "status": status},
        "jobs": [
            {
                "id": j.id,
                "title": j.title,
                "body": j.body,
                "category": j.category,
                "status": j.status,
                "claimed_by": j.claimed_by,
                "created_by": j.created_by,
                "channel": j.channel,
                "summary": j.summary,
                "created_at": j.created_at.isoformat()
            }
            for j in jobs
        ]
    }


@router.post("/jobs/")
async def create_job(
    title: str,
    body: str,
    category: str = "general",
    channel: str = "general",
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_admin_user)
):
    """Create a new job (admin API)."""
    from app.models.chat_job import ChatJob
    from app.api.routes.chat import _save_and_broadcast_message
    
    job = ChatJob(
        title=title,
        body=body,
        category=category,
        channel=channel,
        created_by="admin"
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    
    # Post job card to channel
    job_card = (
        f"[JOB #{job.id[:8]}] {category.upper()} — {title}\n"
        f"{body}\n"
        f"Posted by: admin | Status: open"
    )
    await _save_and_broadcast_message(
        db, channel, "system", job_card, "system"
    )
    
    return {
        "id": job.id,
        "title": job.title,
        "category": job.category,
        "status": job.status,
        "channel": job.channel
    }


@router.post("/jobs/{job_id}/claim/")
async def claim_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_admin_user)
):
    """Claim a job (admin API)."""
    from app.models.chat_job import ChatJob
    from app.models.channel import Channel
    
    result = await db.execute(select(ChatJob).where(ChatJob.id == job_id))
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != "open":
        raise HTTPException(status_code=400, detail=f"Job already {job.status}")
    
    job.status = "claimed"
    job.claimed_by = "admin"
    
    # Create private work channel
    work_channel = f"job-{job.id[:8]}"
    result = await db.execute(select(Channel).where(Channel.name == work_channel))
    if not result.scalar_one_or_none():
        ch = Channel(name=work_channel, private=True, created_by="admin")
        db.add(ch)
    
    await db.commit()
    
    return {
        "id": job.id,
        "status": "claimed",
        "work_channel": work_channel
    }


@router.post("/jobs/{job_id}/done/")
async def job_done(
    job_id: str,
    summary: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_admin_user)
):
    """Mark a job as done (admin API)."""
    from app.models.chat_job import ChatJob
    from app.api.routes.chat import _save_and_broadcast_message
    
    result = await db.execute(select(ChatJob).where(ChatJob.id == job_id))
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job.status = "done"
    job.summary = summary
    await db.commit()
    
    # Post completion
    await _save_and_broadcast_message(
        db, job.channel, "system",
        f"Job #{job.id[:8]} COMPLETED:\n{summary}",
        "system"
    )
    
    return {"id": job.id, "status": "done", "summary": summary}
