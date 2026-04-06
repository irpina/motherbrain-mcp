"""MCP Service API Routes

Routes for registering and managing MCP services.

Extension Points:
    - Add bulk operations for multiple services
    - Add service health check polling
    - Add capability discovery endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import verify_api_key
from app.db.session import get_db
from app.schemas.mcp_service import (
    MCPServiceCreate, 
    MCPServiceResponse, 
    MCPServiceHeartbeat,
    MCPServiceUpdate
)
from app.services import mcp_service_service

router = APIRouter(prefix="/mcp", tags=["mcp"])


@router.post("/register", response_model=MCPServiceResponse)
async def register_mcp_service(
    data: MCPServiceCreate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key)
):
    """Register a new MCP service.
    
    This endpoint registers a new MCP service with Motherbrain,
    making it available for job routing.
    
    Args:
        data: Service registration information
        db: Database session
    
    Returns:
        The registered service
    
    Raises:
        HTTPException 400: If service_id already exists
    """
    # Check if service already exists
    existing = await mcp_service_service.get_service(db, data.service_id)
    if existing:
        raise HTTPException(
            status_code=400, 
            detail=f"Service {data.service_id} already registered"
        )
    
    service = await mcp_service_service.register_service(db, data)
    return service


@router.post("/heartbeat", response_model=MCPServiceResponse)
async def mcp_heartbeat(
    data: MCPServiceHeartbeat,
    db: AsyncSession = Depends(get_db)
):
    """Update MCP service heartbeat.
    
    Services should call this periodically (e.g., every 10-30 seconds)
    to indicate they are still alive.
    
    Args:
        data: Heartbeat data with service_id
        db: Database session
    
    Returns:
        The updated service
    
    Raises:
        HTTPException 404: If service not found
    """
    service = await mcp_service_service.update_heartbeat(db, data.service_id)
    if not service:
        raise HTTPException(
            status_code=404,
            detail=f"Service {data.service_id} not found"
        )
    return service


@router.get("/services", response_model=list[MCPServiceResponse])
async def list_mcp_services(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key)
):
    """List all registered MCP services.
    
    Args:
        db: Database session
    
    Returns:
        List of all MCP services
    """
    return await mcp_service_service.list_services(db)


@router.get("/services/{service_id}", response_model=MCPServiceResponse)
async def get_mcp_service(
    service_id: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key)
):
    """Get a specific MCP service by ID.
    
    Args:
        service_id: The service identifier
        db: Database session
    
    Returns:
        The MCP service
    
    Raises:
        HTTPException 404: If service not found
    """
    service = await mcp_service_service.get_service(db, service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    return service


@router.post("/services/{service_id}/status")
async def update_mcp_service_status(
    service_id: str,
    status: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key)
):
    """Manually update service status (admin only).
    
    Args:
        service_id: The service identifier
        status: New status ("online" or "offline")
        db: Database session
    
    Returns:
        Success message
    """
    service = await mcp_service_service.update_service_status(db, service_id, status)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    return {"status": "updated", "service_id": service_id, "new_status": status}


@router.put("/services/{service_id}", response_model=MCPServiceResponse)
async def update_mcp_service(
    service_id: str,
    data: MCPServiceUpdate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key)
):
    """Update MCP service properties.
    
    Args:
        service_id: The service identifier
        data: Update data (only provided fields are changed)
        db: Database session
    
    Returns:
        The updated service
    """
    service = await mcp_service_service.update_service(db, service_id, data)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    return service


@router.delete("/services/{service_id}")
async def delete_mcp_service(
    service_id: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key)
):
    """Delete an MCP service.
    
    Args:
        service_id: The service identifier
        db: Database session
    
    Returns:
        Success message
    """
    deleted = await mcp_service_service.delete_service(db, service_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Service not found")
    return {"status": "deleted", "service_id": service_id}


# FUTURE: Background task to mark stale services offline
# This would be triggered by a scheduler (APScheduler or similar)
async def cleanup_stale_services_task(db: AsyncSession):
    """Background task to mark stale services as offline.
    
    This should be run periodically (e.g., every 30 seconds).
    """
    count = await mcp_service_service.mark_stale_services_offline(db)
    if count > 0:
        print(f"Marked {count} stale services as offline")
