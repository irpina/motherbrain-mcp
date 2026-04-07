import asyncio
import threading
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.init_db import init_db
from app.api.routes import agents, jobs, context, messages, actions, mcp, system, events
from app.background.heartbeat import start_heartbeat_checker


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize DB and background tasks
    await init_db()
    heartbeat_task = asyncio.create_task(start_heartbeat_checker())
    
    # Start MCP server in background thread (like agentchattr)
    from app.mcp_server import mcp
    mcp_thread = threading.Thread(
        target=mcp.run,
        kwargs={"transport": "streamable-http"},
        daemon=True,
    )
    mcp_thread.start()
    
    yield
    # Shutdown: cancel background tasks cleanly
    heartbeat_task.cancel()


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


@app.get("/health")
async def health_check():
    return {"status": "ok"}
