import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.init_db import init_db
from app.api.routes import agents, jobs, context, messages, actions, mcp, system, events, heartbeat, event_log_routes
from app.background.heartbeat import start_heartbeat_checker
from app.background.health_check import start_health_checker
from app.mcp_server import mcp as mcp_server

# Cache the MCP app and access session manager
_mcp_app = None

def get_mcp_app():
    """Get or create the MCP Starlette app (cached)."""
    global _mcp_app
    if _mcp_app is None:
        _mcp_app = mcp_server.streamable_http_app()
    return _mcp_app


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize DB and background tasks
    await init_db()
    heartbeat_task = asyncio.create_task(start_heartbeat_checker())
    health_task = asyncio.create_task(start_health_checker())
    
    # Start MCP session manager (required for streamable-http transport)
    # This initializes the task group that handles concurrent sessions
    get_mcp_app()  # Ensure app is created
    async with mcp_server.session_manager.run():
        yield
    
    # Shutdown: cancel background tasks cleanly
    heartbeat_task.cancel()
    health_task.cancel()


app = FastAPI(
    title="Motherbrain MCP",
    description="Control plane for agent orchestration",
    version="0.2.0",
    lifespan=lifespan
)

# CORS middleware for dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(agents.router, prefix="/agents", tags=["agents"])
app.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
app.include_router(context.router, prefix="/context", tags=["context"])
app.include_router(messages.router, prefix="/messages", tags=["messages"])
app.include_router(actions.router, prefix="/actions", tags=["actions"])
app.include_router(mcp.router, tags=["mcp"])
app.include_router(system.router)
app.include_router(events.router)
app.include_router(heartbeat.router)
app.include_router(event_log_routes.router)

# Mount MCP server at /mcp (shares FastAPI event loop)
app.mount("/mcp", get_mcp_app())


@app.get("/health")
async def health_check():
    return {"status": "ok"}
