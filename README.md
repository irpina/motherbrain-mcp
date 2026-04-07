# Motherbrain MCP

> A self-hosted MCP hub that connects AI agents to services, routes jobs, and logs everything — in one `docker compose up`.

## What is Motherbrain?

Motherbrain is a coordination hub for AI agents. Connect any MCP-compatible LLM client (Claude Desktop, etc.) to a single endpoint and get:

- **Unified MCP proxy** — one endpoint, all your services
- **Live event log** — every tool call logged with caller identity, args, response, duration
- **Service health monitoring** — auto-probes registered services every 30s
- **Shared context/skill store** — key-value store for prompts, skills, shared state
- **Agent registry** — register agents, deliver triggers via heartbeat
- **Next.js dashboard** — real-time view of services, agents, and activity

## Quick Start

Prerequisites: Docker + Docker Compose

```bash
git clone https://github.com/yourusername/motherbrain-mcp.git
cd motherbrain-mcp
cp .env.example .env
docker compose up -d
```

- API: http://localhost:8000
- Dashboard: http://localhost:3000
- MCP endpoint: http://localhost:8000/mcp

## Connecting an LLM Client

Add Motherbrain to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "motherbrain": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

Restart Claude Desktop. Call `discover()` — Motherbrain introduces itself and walks you through the system.

## MCP Tools

| Tool | Description |
|------|-------------|
| `discover()` | Live orientation — services, agents online, how-to |
| `get_system_state()` | Raw JSON system state |
| `list_tools(service_id)` | List tools on a registered service |
| `call_tool(service_id, tool_name, arguments)` | Proxy a call to any registered service |
| `get_event_log(limit, since_id, topic, service_id)` | Read the unified audit log |
| `get_context(key)` | Fetch a value or skill from the context store |
| `set_context(key, value_json, description)` | Store a value or skill |

## Registering an External MCP Service

```bash
curl -X POST http://localhost:8000/mcp-services/register \
  -H "Content-Type: application/json" \
  -H "X-API-Key: supersecret" \
  -d '{
    "service_id": "my-service",
    "name": "My MCP Service",
    "endpoint": "http://localhost:8010",
    "capabilities": ["tool_a", "tool_b"]
  }'
```

Once registered, Motherbrain will health-probe it every 30s and expose it through `call_tool`.

## Agent Registration & Heartbeat

Agents register with Motherbrain and poll for triggers:

```bash
# Register
curl -X POST http://localhost:8000/agents/register \
  -H "X-API-Key: supersecret" \
  -H "Content-Type: application/json" \
  -d '{"name": "my-agent", "platform": "python", "capabilities": {}}'

# Heartbeat (every 30s) — returns any pending triggers
curl -X POST http://localhost:8000/api/heartbeat/my-agent?agent_id=YOUR_ID
```

## Architecture

```
motherbrain-mcp/
├── app/
│   ├── mcp_server.py        # FastMCP server — 7 tools at /mcp
│   ├── main.py              # FastAPI entry point + lifespan
│   ├── api/routes/          # REST endpoints
│   ├── background/
│   │   ├── heartbeat.py     # Agent liveness checker
│   │   └── health_check.py  # Service health prober (30s)
│   ├── models/              # SQLAlchemy ORM models
│   ├── schemas/             # Pydantic schemas
│   ├── services/            # Business logic
│   └── db/                  # Async database session
├── dashboard/               # Next.js frontend
├── alembic/                 # DB migrations (auto-applied on startup)
├── mock_mcp_server/         # Test MCP server for local dev
├── docker-compose.yml
├── Dockerfile
└── .env.example
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://postgres:postgres@db:5432/motherbrain` |
| `REDIS_URL` | Redis connection string | `redis://redis:6379` |
| `API_KEY` | Master API key (change in production) | `supersecret` |

## Development

```bash
make up      # Start all services
make down    # Stop
make logs    # Follow logs
make shell   # Shell into API container
```

Mock MCP server for testing without external services:
```bash
cd mock_mcp_server && python main.py  # Runs on port 8001
```

Database migrations:
```bash
alembic revision -m "description"   # Create
alembic upgrade head                 # Apply
alembic downgrade -1                 # Rollback
```

## License

MIT
