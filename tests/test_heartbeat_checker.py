"""Tests for the heartbeat staleness checker.

These tests verify that services are correctly marked offline when
they haven't sent a heartbeat within the configured timeout.
"""

from datetime import datetime, timezone, timedelta

from app.services.mcp_service_service import (
    register_service,
    update_heartbeat,
    mark_stale_services_offline
)
from app.models.mcp_service import MCPService
from app.schemas.mcp_service import MCPServiceCreate


async def test_stale_service_marked_offline(db_session):
    """Test that a service with an old heartbeat is marked offline.
    
    A service that last heartbeat-ed 120 seconds ago should be marked
    offline when the max age is 60 seconds.
    """
    # Register a service
    service = await register_service(db_session, MCPServiceCreate(
        service_id="stale-1",
        name="Stale Service",
        endpoint="http://stale",
        capabilities=[],
        api_key=None
    ))
    
    # Manually set heartbeat to 120 seconds ago (simulating old heartbeat)
    service.last_heartbeat = datetime.now(timezone.utc) - timedelta(seconds=120)
    service.status = "online"
    await db_session.commit()
    
    # Run staleness check
    count = await mark_stale_services_offline(db_session, max_age_seconds=60)
    assert count == 1
    
    # Verify service is now offline
    await db_session.refresh(service)
    assert service.status == "offline"


async def test_fresh_service_stays_online(db_session):
    """Test that a recently heartbeated service stays online.
    
    A service that heartbeated 10 seconds ago should NOT be marked
    offline when the max age is 60 seconds.
    """
    # Register and heartbeat a service
    service = await register_service(db_session, MCPServiceCreate(
        service_id="fresh-1",
        name="Fresh Service",
        endpoint="http://fresh",
        capabilities=[],
        api_key=None
    ))
    await update_heartbeat(db_session, "fresh-1")
    
    # Manually adjust heartbeat to 10 seconds ago
    service.last_heartbeat = datetime.now(timezone.utc) - timedelta(seconds=10)
    await db_session.commit()
    
    # Run staleness check
    count = await mark_stale_services_offline(db_session, max_age_seconds=60)
    assert count == 0
    
    # Verify service is still online
    await db_session.refresh(service)
    assert service.status == "online"


async def test_null_heartbeat_service_marked_offline(db_session):
    """Test that a service with NULL last_heartbeat is marked offline.
    
    This covers the edge case where a service is manually set to online
    but has never sent a heartbeat.
    """
    # Create service directly with NULL heartbeat but online status
    service = MCPService(
        service_id="null-hb",
        name="No Heartbeat",
        endpoint="http://nohb",
        capabilities=[],
        status="online",  # Manually set online
        last_heartbeat=None  # Never sent heartbeat
    )
    db_session.add(service)
    await db_session.commit()
    
    # Run staleness check
    count = await mark_stale_services_offline(db_session, max_age_seconds=60)
    assert count == 1
    
    # Verify service is now offline
    await db_session.refresh(service)
    assert service.status == "offline"


async def test_offline_services_ignored(db_session):
    """Test that already-offline services are not counted in the staleness check."""
    # Create an already-offline service with old heartbeat
    service = MCPService(
        service_id="already-offline",
        name="Already Offline",
        endpoint="http://offline",
        capabilities=[],
        status="offline",
        last_heartbeat=datetime.now(timezone.utc) - timedelta(seconds=300)
    )
    db_session.add(service)
    await db_session.commit()
    
    # Run staleness check
    count = await mark_stale_services_offline(db_session, max_age_seconds=60)
    assert count == 0  # Should not count already-offline services


async def test_multiple_stale_services(db_session):
    """Test that multiple stale services are all marked offline."""
    # Create multiple stale services
    for i in range(3):
        service = MCPService(
            service_id=f"stale-{i}",
            name=f"Stale {i}",
            endpoint=f"http://stale-{i}",
            capabilities=[],
            status="online",
            last_heartbeat=datetime.now(timezone.utc) - timedelta(seconds=120)
        )
        db_session.add(service)
    
    await db_session.commit()
    
    # Run staleness check
    count = await mark_stale_services_offline(db_session, max_age_seconds=60)
    assert count == 3


async def test_mixed_fresh_and_stale_services(db_session):
    """Test that only stale services are marked offline when mixing fresh and stale."""
    # Create a fresh service
    fresh = MCPService(
        service_id="fresh-mixed",
        name="Fresh Mixed",
        endpoint="http://fresh-mixed",
        capabilities=[],
        status="online",
        last_heartbeat=datetime.now(timezone.utc) - timedelta(seconds=10)
    )
    db_session.add(fresh)
    
    # Create a stale service
    stale = MCPService(
        service_id="stale-mixed",
        name="Stale Mixed",
        endpoint="http://stale-mixed",
        capabilities=[],
        status="online",
        last_heartbeat=datetime.now(timezone.utc) - timedelta(seconds=120)
    )
    db_session.add(stale)
    
    await db_session.commit()
    
    # Run staleness check
    count = await mark_stale_services_offline(db_session, max_age_seconds=60)
    assert count == 1  # Only the stale one
    
    # Verify correct service was marked offline
    await db_session.refresh(fresh)
    await db_session.refresh(stale)
    assert fresh.status == "online"
    assert stale.status == "offline"


async def test_exact_threshold_boundary(db_session):
    """Test the exact boundary of the staleness threshold."""
    # Service exactly at threshold (should be marked offline)
    service = MCPService(
        service_id="boundary",
        name="Boundary",
        endpoint="http://boundary",
        capabilities=[],
        status="online",
        last_heartbeat=datetime.now(timezone.utc) - timedelta(seconds=60)
    )
    db_session.add(service)
    await db_session.commit()
    
    # With max_age=60, a heartbeat from exactly 60 seconds ago is stale
    count = await mark_stale_services_offline(db_session, max_age_seconds=60)
    assert count == 1
