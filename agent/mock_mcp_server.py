"""
mock_mcp_server.py — Local MCP Server for Testing

A minimal FastAPI server that mimics an MCP service. Use this to test
Motherbrain's MCP routing layer without needing a real external MCP server.

Capabilities exposed:
  - "echo"           → returns the input payload
  - "generate_code"  → returns a stub code response
  - "shell"          → simulates shell execution (no actual exec)

Usage:
  # Terminal 1 — start Motherbrain
  make up

  # Terminal 2 — start this mock server
  cd agent
  uvicorn mock_mcp_server:app --port 8001 --reload

  # Terminal 3 — register the mock server with Motherbrain
  curl -X POST http://localhost:8000/mcp/register \\
    -H "X-API-Key: supersecret" \\
    -H "Content-Type: application/json" \\
    -d '{
      "service_id": "mock-mcp-1",
      "name": "Mock MCP Server",
      "endpoint": "http://localhost:8001",
      "capabilities": ["echo", "generate_code", "shell"]
    }'

  # Send heartbeat
  curl -X POST http://localhost:8000/mcp/heartbeat \\
    -H "X-API-Key: supersecret" \\
    -H "Content-Type: application/json" \\
    -d '{"service_id": "mock-mcp-1"}'

  # Create a job routed to MCP
  curl -X POST http://localhost:8000/jobs \\
    -H "X-API-Key: supersecret" \\
    -H "Content-Type: application/json" \\
    -d '{
      "type": "generate_code",
      "target_type": "mcp",
      "requirements": ["generate_code"],
      "payload": {"prompt": "Create a FastAPI health check endpoint"}
    }'
"""

import time
from fastapi import FastAPI, Request
from pydantic import BaseModel

app = FastAPI(title="Mock MCP Server", version="1.0.0")


class ExecuteRequest(BaseModel):
    job_id: str
    type: str
    payload: dict = {}


@app.get("/health")
async def health():
    """Health check — Motherbrain may poll this to verify reachability."""
    return {"status": "ok", "service": "mock-mcp-server"}


@app.post("/execute")
async def execute(request: ExecuteRequest):
    """
    Execute a job forwarded by Motherbrain.

    Motherbrain calls this endpoint when routing a job with target_type="mcp".
    The response is stored in job.result.

    Extension point: replace the mock logic below with real tool execution.
    """
    job_type = request.type
    payload = request.payload

    # Simulate processing time
    time.sleep(0.1)

    # Dispatch by job type — add new handlers here for new capabilities
    if job_type == "echo":
        result = {"echo": payload}

    elif job_type == "generate_code":
        prompt = payload.get("prompt", "")
        result = {
            "code": f"# Generated for: {prompt}\ndef solution():\n    pass",
            "language": "python",
        }

    elif job_type == "shell":
        command = payload.get("command", "echo hello")
        # STUB: does not execute real commands — safe for testing
        result = {
            "stdout": f"[mock] would run: {command}",
            "stderr": "",
            "exit_code": 0,
        }

    else:
        # Unknown type — return generic success so routing tests still pass
        result = {
            "message": f"[mock] processed job type '{job_type}'",
            "payload_received": payload,
        }

    return {
        "job_id": request.job_id,
        "status": "completed",
        "result": result,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
