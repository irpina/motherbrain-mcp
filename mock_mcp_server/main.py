"""Mock MCP Server for Testing

A simple FastAPI server that implements the MCP service protocol
for testing Motherbrain's MCP routing layer without external dependencies.

Usage:
    cd mock_mcp_server
    python main.py  # Runs on port 8001

Or with Docker:
    docker run -p 8001:8000 mock-mcp-server
"""

import os
import time
from datetime import datetime, timezone
from typing import Optional

import uvicorn
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Mock MCP Server", version="0.1.0")

# In-memory state (would be DB in production)
EXECUTIONS = []


class ExecuteRequest(BaseModel):
    """Request to execute a task."""
    job_id: str
    payload: dict


class ExecuteResponse(BaseModel):
    """Response from task execution."""
    job_id: str
    result: dict
    execution_time_ms: float
    timestamp: str


class HeartbeatResponse(BaseModel):
    """Heartbeat response."""
    status: str
    service_id: str
    timestamp: str


# Mock service configuration
SERVICE_ID = os.getenv("MCP_SERVICE_ID", "mock-mcp-001")
API_KEY = os.getenv("MCP_API_KEY", "mock-secret-key")
CAPABILITIES = ["generate_code", "text_completion", "summarize"]


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "service": "Mock MCP Server",
        "service_id": SERVICE_ID,
        "capabilities": CAPABILITIES,
        "status": "online"
    }


@app.post("/execute", response_model=ExecuteResponse)
async def execute(
    request: ExecuteRequest,
    x_api_key: Optional[str] = Header(None)
):
    """Execute a task.
    
    This is the main endpoint that Motherbrain calls to route jobs
    to this MCP service.
    
    Args:
        request: The execution request with job_id and payload
        x_api_key: API key for authentication
    
    Returns:
        Execution result with timing information
    """
    # Verify API key
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    
    start_time = time.time()
    
    # Mock execution based on payload
    task_type = request.payload.get("type", "unknown")
    
    if task_type == "generate_code":
        result = {
            "code": "def hello_world():\n    print('Hello, World!')",
            "language": "python",
            "explanation": "A simple greeting function"
        }
    elif task_type == "summarize":
        text = request.payload.get("text", "")
        result = {
            "summary": text[:100] + "..." if len(text) > 100 else text,
            "original_length": len(text),
            "summary_length": min(len(text), 100)
        }
    else:
        # Default echo response
        result = {
            "echo": request.payload,
            "message": "Task processed by Mock MCP Server",
            "capabilities_used": CAPABILITIES[:2]
        }
    
    execution_time = (time.time() - start_time) * 1000
    
    # Record execution
    EXECUTIONS.append({
        "job_id": request.job_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "execution_time_ms": execution_time
    })
    
    return ExecuteResponse(
        job_id=request.job_id,
        result=result,
        execution_time_ms=execution_time,
        timestamp=datetime.now(timezone.utc).isoformat()
    )


@app.post("/heartbeat", response_model=HeartbeatResponse)
async def heartbeat():
    """Heartbeat endpoint for health checks.
    
    Motherbrain calls this (via POST to /mcp/heartbeat) to verify
    the service is still alive.
    """
    return HeartbeatResponse(
        status="ok",
        service_id=SERVICE_ID,
        timestamp=datetime.now(timezone.utc).isoformat()
    )


@app.get("/executions")
async def list_executions():
    """List all executions (for debugging)."""
    return {
        "total": len(EXECUTIONS),
        "executions": EXECUTIONS[-10:]  # Last 10
    }


@app.get("/capabilities")
async def list_capabilities():
    """List available capabilities."""
    return {
        "service_id": SERVICE_ID,
        "capabilities": CAPABILITIES
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8001"))
    print(f"Starting Mock MCP Server on port {port}")
    print(f"Service ID: {SERVICE_ID}")
    print(f"Capabilities: {CAPABILITIES}")
    uvicorn.run(app, host="0.0.0.0", port=port)
