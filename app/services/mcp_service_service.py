"""MCP Service Business Logic

This module contains the business logic for managing MCP services,
including registration, heartbeat handling, and service discovery.
"""

import hashlib
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mcp_service import MCPService
from app.schemas.mcp_service import MCPServiceCreate, MCPServiceUpdate


async def register_service(
    db: AsyncSession, 
    data: MCPServiceCreate
) -> MCPService:
    """Register a new MCP service.
    
    Args:
        db: Database session
        data: Service registration data
    
    Returns:
        The created MCPService instance
    """
    # Hash API key if provided
    api_key_hash = None
    if data.api_key:
        api_key_hash = hashlib.sha256(data.api_key.encode()).hexdigest()
    
    service = MCPService(
        service_id=data.service_id,
        name=data.name,
        endpoint=data.endpoint,
        capabilities=data.capabilities,
        status="offline",    # Becomes "online" after the first heartbeat
        last_heartbeat=None,
        api_key_hash=api_key_hash,
        protocol=data.protocol
    )
    
    db.add(service)
    await db.commit()
    await db.refresh(service)
    return service


async def get_service(db: AsyncSession, service_id: str) -> Optional[MCPService]:
    """Get an MCP service by ID.
    
    Args:
        db: Database session
        service_id: The service identifier
    
    Returns:
        The MCPService or None if not found
    """
    result = await db.execute(
        select(MCPService).where(MCPService.service_id == service_id)
    )
    return result.scalar_one_or_none()


async def list_services(db: AsyncSession) -> list[MCPService]:
    """List all registered MCP services.
    
    Args:
        db: Database session
    
    Returns:
        List of all MCP services
    """
    result = await db.execute(select(MCPService))
    return list(result.scalars().all())


async def update_heartbeat(db: AsyncSession, service_id: str) -> Optional[MCPService]:
    """Update the heartbeat timestamp for a service.
    
    Also sets status to "online" if it was offline.
    
    Args:
        db: Database session
        service_id: The service identifier
    
    Returns:
        The updated service or None if not found
    """
    service = await get_service(db, service_id)
    if not service:
        return None
    
    service.last_heartbeat = datetime.now(timezone.utc)
    service.status = "online"
    
    await db.commit()
    await db.refresh(service)
    return service


async def update_service_status(
    db: AsyncSession, 
    service_id: str, 
    status: str
) -> Optional[MCPService]:
    """Update the status of a service.
    
    Args:
        db: Database session
        service_id: The service identifier
        status: New status ("online" or "offline")
    
    Returns:
        The updated service or None if not found
    """
    service = await get_service(db, service_id)
    if not service:
        return None
    
    service.status = status
    await db.commit()
    await db.refresh(service)
    return service


async def update_service(
    db: AsyncSession,
    service_id: str,
    data: MCPServiceUpdate
) -> Optional[MCPService]:
    """Update service properties.
    
    Args:
        db: Database session
        service_id: The service identifier
        data: Update data (only provided fields are updated)
    
    Returns:
        The updated service or None if not found
    """
    service = await get_service(db, service_id)
    if not service:
        return None
    
    if data.name is not None:
        service.name = data.name
    if data.endpoint is not None:
        service.endpoint = data.endpoint
    if data.capabilities is not None:
        service.capabilities = data.capabilities
    if data.protocol is not None:
        service.protocol = data.protocol
    
    await db.commit()
    await db.refresh(service)
    return service


async def delete_service(db: AsyncSession, service_id: str) -> bool:
    """Delete an MCP service.
    
    Args:
        db: Database session
        service_id: The service identifier
    
    Returns:
        True if deleted, False if not found
    """
    service = await get_service(db, service_id)
    if not service:
        return False
    
    await db.delete(service)
    await db.commit()
    return True


async def mark_stale_services_offline(db: AsyncSession, max_age_seconds: int = 60) -> int:
    """Mark services as offline if they haven't sent a heartbeat recently.
    
    This should be called periodically (e.g., every 30 seconds) to
    ensure the service registry reflects actual availability.
    
    Also catches services that are "online" but have never sent a heartbeat
    (last_heartbeat IS NULL).
    
    Args:
        db: Database session
        max_age_seconds: Maximum age of heartbeat before marking offline
    
    Returns:
        Number of services marked offline
    """
    from datetime import timedelta
    from sqlalchemy import or_
    
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=max_age_seconds)
    
    result = await db.execute(
        select(MCPService).where(
            MCPService.status == "online",
            or_(
                MCPService.last_heartbeat.is_(None),
                MCPService.last_heartbeat < cutoff
            )
        )
    )
    
    stale_services = result.scalars().all()
    count = 0
    
    for service in stale_services:
        service.status = "offline"
        count += 1
    
    if count > 0:
        await db.commit()
    
    return count
