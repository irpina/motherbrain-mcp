"""
heartbeat.py — Stale Service Cleanup Background Task

Runs on a periodic interval and marks any MCP service "offline" if
its last_heartbeat is older than HEARTBEAT_TIMEOUT_SECONDS (60s).

This is the mechanism that keeps the service registry accurate.
Without it, services that crash without sending a goodbye would
stay "online" indefinitely and receive routed jobs they can't handle.

Wiring into main.py (add to lifespan):

    from app.background.heartbeat import start_heartbeat_checker

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await init_db()
        task = asyncio.create_task(start_heartbeat_checker())
        yield
        task.cancel()

Extension points:
  - Adjust CHECK_INTERVAL_SECONDS to tune responsiveness vs DB load
  - Add alerting/logging when services flip offline
  - Add a "grace period" counter before marking offline (n missed beats)
"""

import asyncio
import logging

from app.db.session import AsyncSessionLocal
from app.services.mcp_service_service import mark_stale_services_offline

logger = logging.getLogger(__name__)

# How often to run the staleness check (seconds)
CHECK_INTERVAL_SECONDS = 30


async def start_heartbeat_checker() -> None:
    """
    Infinite loop that periodically marks stale MCP services offline.

    Designed to run as a background asyncio task alongside the FastAPI app.
    Catches and logs all exceptions so a single DB error doesn't kill the loop.
    """
    logger.info(
        "Heartbeat checker started — checking every %ds, "
        "offline threshold: 60s",
        CHECK_INTERVAL_SECONDS,
    )

    while True:
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)
        try:
            async with AsyncSessionLocal() as db:
                count = await mark_stale_services_offline(db)
                if count > 0:
                    logger.warning(
                        "Heartbeat checker: marked %d stale MCP service(s) offline",
                        count,
                    )
        except Exception:
            # Log but keep running — a transient DB error should not stop the checker
            logger.exception("Heartbeat checker encountered an error")
