"""Tests for MCP service registration and heartbeat endpoints.

These tests verify that MCP services can be registered, listed,
and marked online/offline via heartbeat updates.
"""

import pytest


async def test_register_mcp_service(client):
    """Test registering a new MCP service.
    
    The service should be created with status "offline" and no
    last_heartbeat until it sends its first heartbeat.
    """
    response = await client.post("/mcp/register", json={
        "service_id": "test-mcp-1",
        "name": "Test Service",
        "endpoint": "http://localhost:8001",
        "capabilities": ["echo", "generate_code"]
    })
    assert response.status_code == 200
    data = response.json()
    assert data["service_id"] == "test-mcp-1"
    assert data["name"] == "Test Service"
    assert data["endpoint"] == "http://localhost:8001"
    assert data["capabilities"] == ["echo", "generate_code"]
    assert data["status"] == "offline"  # Must be offline until heartbeat
    assert data["last_heartbeat"] is None


async def test_register_duplicate_returns_400(client):
    """Test that duplicate service_id returns 400 error."""
    payload = {
        "service_id": "dup-1",
        "name": "X",
        "endpoint": "http://x",
        "capabilities": []
    }
    # First registration succeeds
    response1 = await client.post("/mcp/register", json=payload)
    assert response1.status_code == 200
    
    # Second registration with same ID fails
    response2 = await client.post("/mcp/register", json=payload)
    assert response2.status_code == 400
    assert "already registered" in response2.json()["detail"].lower()


async def test_heartbeat_sets_online(client):
    """Test that heartbeat updates status to online and sets timestamp."""
    # First register the service
    await client.post("/mcp/register", json={
        "service_id": "hb-test",
        "name": "HB",
        "endpoint": "http://hb",
        "capabilities": []
    })
    
    # Send heartbeat
    response = await client.post("/mcp/heartbeat", json={"service_id": "hb-test"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["last_heartbeat"] is not None


async def test_heartbeat_unknown_service(client):
    """Test that heartbeat for unknown service returns 404."""
    response = await client.post("/mcp/heartbeat", json={"service_id": "ghost"})
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


async def test_list_services(client):
    """Test listing all registered MCP services."""
    # Register multiple services
    for i in range(3):
        await client.post("/mcp/register", json={
            "service_id": f"svc-{i}",
            "name": f"Service {i}",
            "endpoint": f"http://svc-{i}",
            "capabilities": []
        })
    
    response = await client.get("/mcp/services")
    assert response.status_code == 200
    services = response.json()
    assert len(services) == 3
    
    # Verify service IDs are present
    service_ids = {s["service_id"] for s in services}
    assert service_ids == {"svc-0", "svc-1", "svc-2"}


async def test_get_single_service(client):
    """Test getting a specific service by ID."""
    await client.post("/mcp/register", json={
        "service_id": "single-svc",
        "name": "Single",
        "endpoint": "http://single",
        "capabilities": ["test"]
    })
    
    response = await client.get("/mcp/services/single-svc")
    assert response.status_code == 200
    data = response.json()
    assert data["service_id"] == "single-svc"
    assert data["name"] == "Single"


async def test_get_unknown_service_returns_404(client):
    """Test that getting an unknown service returns 404."""
    response = await client.get("/mcp/services/nonexistent")
    assert response.status_code == 404


async def test_update_service(client):
    """Test updating service properties."""
    await client.post("/mcp/register", json={
        "service_id": "update-svc",
        "name": "Original",
        "endpoint": "http://original",
        "capabilities": ["a", "b"]
    })
    
    response = await client.put("/mcp/services/update-svc", json={
        "name": "Updated",
        "capabilities": ["c", "d"]
    })
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated"
    assert data["capabilities"] == ["c", "d"]
    assert data["endpoint"] == "http://original"  # Unchanged


async def test_delete_service(client):
    """Test deleting a service."""
    await client.post("/mcp/register", json={
        "service_id": "delete-svc",
        "name": "ToDelete",
        "endpoint": "http://delete",
        "capabilities": []
    })
    
    response = await client.delete("/mcp/services/delete-svc")
    assert response.status_code == 200
    assert response.json()["status"] == "deleted"
    
    # Verify it's gone
    get_response = await client.get("/mcp/services/delete-svc")
    assert get_response.status_code == 404
