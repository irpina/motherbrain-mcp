"""Agent terminal API for live shell access to spawned containers.

Provides token-based authentication and WebSocket bridge for terminal
access to running agent containers using docker exec.
"""
from __future__ import annotations
import os
import asyncio
import subprocess
from datetime import datetime, timezone
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import require_admin_user
from app.db.session import get_db
from app.models.spawned_agent import SpawnedAgent
from app.queue.redis_queue import set_key, get_key, delete_key

router = APIRouter(prefix="/agents", tags=["agent-terminal"])


TERMINAL_TOKEN_TTL = 60  # seconds


@router.post("/spawned/{agent_id}/terminal-token/")
async def create_terminal_token(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_admin_user)
):
    """Create a single-use terminal access token for a spawned agent.
    
    The token is valid for 60 seconds and can only be used once.
    """
    # Get the spawned agent
    result = await db.execute(
        select(SpawnedAgent).where(SpawnedAgent.id == agent_id)
    )
    spawned = result.scalar_one_or_none()
    
    if not spawned:
        raise HTTPException(status_code=404, detail="Spawned agent not found")
    
    if spawned.status != "running":
        raise HTTPException(status_code=400, detail="Agent is not running")
    
    # Generate token
    token = str(uuid4())
    
    # Store token in Redis with container_id
    token_data = {
        "agent_id": agent_id,
        "container_id": spawned.container_id,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await set_key(
        f"terminal_token:{token}",
        str(token_data),
        ttl=TERMINAL_TOKEN_TTL
    )
    
    return {
        "token": token,
        "expires_in": TERMINAL_TOKEN_TTL,
        "agent_id": agent_id,
        "container_id": spawned.container_id[:12]
    }


@router.websocket("/spawned/{agent_id}/terminal-ws")
async def terminal_websocket(
    websocket: WebSocket,
    agent_id: str,
    token: str | None = None
):
    """WebSocket endpoint for terminal access to a spawned agent container.
    
    Connects to the container via `docker exec` and bridges stdin/stdout
    between the WebSocket and the subprocess.
    
    Query params:
        token: Single-use terminal token from POST /terminal-token/
    """
    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return
    
    # Validate and consume token
    token_key = f"terminal_token:{token}"
    token_data_str = await get_key(token_key)
    
    if not token_data_str:
        await websocket.close(code=4002, reason="Invalid or expired token")
        return
    
    # Parse token data
    try:
        # Convert string representation of dict back to dict
        import ast
        token_data = ast.literal_eval(token_data_str)
        container_id = token_data.get("container_id")
        token_agent_id = token_data.get("agent_id")
    except (ValueError, SyntaxError):
        await websocket.close(code=4003, reason="Invalid token format")
        return
    
    # Verify agent_id matches
    if token_agent_id != agent_id:
        await websocket.close(code=4004, reason="Token mismatch")
        return
    
    # Consume token (delete it)
    await delete_key(token_key)
    
    # Accept WebSocket connection
    await websocket.accept()
    
    # Start docker exec process
    try:
        proc = await asyncio.create_subprocess_exec(
            "docker", "exec", "-i", container_id, "/bin/sh",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT
        )
    except Exception as e:
        await websocket.send_text(f"\r\n[Error starting terminal: {e}]\r\n")
        await websocket.close()
        return
    
    # Pump tasks
    async def ws_to_proc():
        """Forward WebSocket messages to process stdin."""
        try:
            while True:
                message = await websocket.receive_text()
                # Handle special terminal sequences if needed
                proc.stdin.write(message.encode())
                await proc.stdin.drain()
        except WebSocketDisconnect:
            pass
        except Exception:
            pass
        finally:
            try:
                proc.stdin.close()
            except:
                pass
    
    async def proc_to_ws():
        """Forward process stdout to WebSocket."""
        try:
            while True:
                chunk = await proc.stdout.read(1024)
                if not chunk:
                    break
                await websocket.send_text(chunk.decode(errors="replace"))
        except Exception:
            pass
        finally:
            try:
                await websocket.close()
            except:
                pass
    
    # Run both pumps concurrently
    try:
        await asyncio.gather(ws_to_proc(), proc_to_ws())
    finally:
        # Clean up process
        try:
            proc.terminate()
            await asyncio.wait_for(proc.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            proc.kill()
        except:
            pass
