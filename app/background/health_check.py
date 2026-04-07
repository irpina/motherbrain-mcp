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
from app.services.mcp_service_service import list_services, update_service_status

logger = logging.getLogger(__name__)
CHECK_INTERVAL_SECONDS = 30
PROBE_TIMEOUT_SECONDS = 5


async def _probe(endpoint: str) -> bool:
    """Return True if the endpoint responds to HTTP (any status code)."""
    url = endpoint.rstrip("/") + "/mcp"
    try:
        async with httpx.AsyncClient(timeout=PROBE_TIMEOUT_SECONDS) as client:
            await client.get(url)
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
                alive = await _probe(svc.endpoint)
                new_status = "online" if alive else "offline"
                if svc.status != new_status:
                    async with AsyncSessionLocal() as db:
                        await update_service_status(db, svc.service_id, new_status)
                    logger.info("Service %s → %s", svc.service_id, new_status)
        except Exception:
            logger.exception("Health checker error")
