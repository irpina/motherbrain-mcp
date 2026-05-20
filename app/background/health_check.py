"""
health_check.py — Active HTTP Health Probe for Registered MCP Services

Runs every CHECK_INTERVAL_SECONDS. For each registered service:
- Makes a GET request to {service.endpoint}/mcp (or just {service.endpoint})
- Any HTTP response (2xx, 4xx, 405, etc.) = service is alive → set online
- Timeout or connection error = service is unreachable → set offline

Unlike the heartbeat checker (which waits for services to phone home),
this probes outbound — so external services like supergateway are covered.
"""
import asyncio
import logging
import httpx
from app.db.session import AsyncSessionLocal
from app.services.mcp_service_service import list_services, update_service_status, update_heartbeat

logger = logging.getLogger(__name__)
CHECK_INTERVAL_SECONDS = 30
PROBE_TIMEOUT_SECONDS = 5


async def _probe(endpoint: str, mcp_path: str = "/mcp") -> bool:
    """Return True if the endpoint responds to HTTP (any status code)."""
    from urllib.parse import urlparse
    path = (mcp_path or "/mcp").rstrip("/") or "/"
    url = endpoint.rstrip("/") + path
    parsed = urlparse(endpoint)
    port_str = f":{parsed.port}" if parsed.port else ""
    # Override Host to localhost so DNS-rebinding protection accepts our probe
    headers = {"Host": f"localhost{port_str}"}
    try:
        async with httpx.AsyncClient(timeout=PROBE_TIMEOUT_SECONDS) as client:
            await client.get(url, headers=headers)
        return True
    except Exception:
        return False


async def start_health_checker() -> None:
    logger.info("Health checker started — probing every %ds", CHECK_INTERVAL_SECONDS)
    while True:
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)
        try:
            async with AsyncSessionLocal() as db:
                services = await list_services(db)
            for svc in services:
                if not svc.endpoint:
                    continue
                alive = await _probe(svc.endpoint, svc.mcp_path or "/mcp")
                new_status = "online" if alive else "offline"
                async with AsyncSessionLocal() as db:
                    if alive:
                        # Refreshing last_heartbeat prevents the heartbeat checker
                        # from marking externally-probed services as stale
                        await update_heartbeat(db, svc.service_id)
                    elif svc.status != "offline":
                        await update_service_status(db, svc.service_id, "offline")
                if svc.status != new_status:
                    logger.info("Service %s → %s", svc.service_id, new_status)
        except Exception:
            logger.exception("Health checker error")
