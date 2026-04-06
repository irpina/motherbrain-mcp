# Mock MCP Server

A simple FastAPI server for testing Motherbrain's MCP routing layer without needing real MCP services.

## Features

- `/execute` — Main task execution endpoint
- `/heartbeat` — Health check endpoint
- `/capabilities` — List available capabilities
- `/executions` — Debug endpoint to see processed jobs

## Quick Start

```bash
# Install dependencies
pip install fastapi uvicorn pydantic

# Run the server
python main.py
```

Server will start on `http://localhost:8001`

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `MCP_SERVICE_ID` | `mock-mcp-001` | Service identifier |
| `MCP_API_KEY` | `mock-secret-key` | API key for auth |
| `PORT` | `8001` | Server port |

## Register with Motherbrain

```bash
# Register this mock service
curl -X POST http://localhost:8000/mcp/register \
  -H "Content-Type: application/json" \
  -H "X-API-Key: supersecret" \
  -d '{
    "service_id": "mock-mcp-001",
    "name": "Mock MCP Server",
    "endpoint": "http://localhost:8001",
    "capabilities": ["generate_code", "text_completion", "summarize"],
    "api_key": "mock-secret-key"
  }'
```

## Test Execution

```bash
# Create a job routed to MCP
curl -X POST http://localhost:8000/jobs/ \
  -H "Content-Type: application/json" \
  -H "X-API-Key: supersecret" \
  -d '{
    "type": "generate_code",
    "target_type": "mcp",
    "requirements": ["generate_code"],
    "payload": {"type": "generate_code", "language": "python"}
  }'
```

## Docker

```bash
docker build -t mock-mcp-server .
docker run -p 8001:8000 -e MCP_SERVICE_ID=my-mock mock-mcp-server
```
