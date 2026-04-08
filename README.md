# Motherbrain MCP

> A self-hosted MCP hub that connects AI agents to services, routes jobs, and logs everything — in one `docker compose up`.

## What is Motherbrain?

Motherbrain is a coordination hub for AI agents. Connect any MCP-compatible LLM client (Claude Desktop, etc.) to a single endpoint and get:

- **Unified MCP proxy** — one endpoint, all your registered services
- **RBAC permission system** — users, groups, and per-service access control
- **Live event log** — every tool call logged with caller identity, args, response, duration
- **Service health monitoring** — auto-probes registered services every 30s with capability auto-discovery
- **Job dispatch** — create and track jobs routed to specific agents or services
- **Shared context/skill store** — key-value store for prompts, skills, shared state
- **Agent registry** — register agents, deliver triggers via heartbeat
- **Next.js dashboard** — real-time view of services, agents, jobs, activity, and admin controls

## Quick Start

Prerequisites: Docker + Docker Compose

```bash
git clone https://github.com/irpina/motherbrain-mcp.git
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

### With User Token (RBAC)

If you've enabled the permission system, pass your user token via header:

```json
{
  "mcpServers": {
    "motherbrain": {
      "url": "http://localhost:8000/mcp",
      "headers": {
        "X-User-Token": "mb_your_token_here"
      }
    }
  }
}
```

Alternatively, call `authenticate(token)` from within a session to bind your identity.

## MCP Tools

| Tool | Description |
|------|-------------|
| `discover()` | Live orientation — services, agents online, how-to |
| `get_system_state()` | Raw JSON system state |
| `list_tools(service_id)` | List tools on a registered service |
| `call_tool(service_id, tool_name, arguments)` | Proxy a call to any registered service |
| `register_service(service_id, name, endpoint, api_key?)` | Register an MCP service — auto-discovers capabilities |
| `remove_service(service_id)` | Deregister a service |
| `create_job(type, payload, requirements?, priority?, assigned_agent?)` | Dispatch a job to an agent |
| `get_job_status(job_id)` | Check job status and result |
| `authenticate(token)` | Bind a user token to the current session (RBAC) |
| `get_event_log(limit, since_id, topic, service_id)` | Read the unified audit log |
| `get_context(key)` | Fetch a value or skill from the context store |
| `set_context(key, value_json, description)` | Store a value or skill |

## Permission System (RBAC)

Motherbrain includes a full role-based access control system for scoping which MCP services each user can access.

**Concepts:**
- **Users** — identified by `mb_` prefixed tokens (SHA-256 hashed in DB). Roles: `user` or `admin`.
- **Groups** — named collections with an `allowed_service_ids` list.
- **Membership** — users belong to groups; groups grant access to services.
- **Admin bypass** — admin-role users can call any service regardless of group membership.

**Setup via API:**

```bash
# Create a user (returns one-time token)
curl -X POST http://localhost:8000/admin/users \
  -H "X-API-Key: supersecret" \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice", "email": "alice@example.com", "role": "user"}'

# Create a group scoped to a service
curl -X POST http://localhost:8000/admin/groups \
  -H "X-API-Key: supersecret" \
  -H "Content-Type: application/json" \
  -d '{"name": "dev-team", "allowed_service_ids": ["filesystem", "fetch"]}'

# Add user to group
curl -X POST http://localhost:8000/admin/users/{user_id}/groups/{group_id} \
  -H "X-API-Key: supersecret"
```

Users and groups can also be managed via the **Admin** section of the dashboard.

## Registering an External MCP Service

```bash
curl -X POST http://localhost:8000/mcp/register \
  -H "Content-Type: application/json" \
  -H "X-API-Key: supersecret" \
  -d '{
    "service_id": "my-service",
    "name": "My MCP Service",
    "endpoint": "http://host.docker.internal:8010"
  }'
```

Motherbrain performs a full MCP handshake to auto-discover the service's capabilities, then health-probes it every 30s.

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
│   ├── mcp_server.py        # FastMCP server — 12 MCP tools at /mcp
│   ├── main.py              # FastAPI entry point + lifespan
│   ├── middleware/
│   │   └── mcp_auth.py      # X-User-Token header extraction (ContextVar)
│   ├── api/routes/
│   │   ├── admin.py         # /admin/users + /admin/groups (API key required)
│   │   └── ...              # agents, jobs, context, events, mcp, system
│   ├── background/
│   │   ├── heartbeat.py     # Agent liveness checker
│   │   └── health_check.py  # Service health prober (30s)
│   ├── models/              # SQLAlchemy ORM models (agents, jobs, users, groups)
│   ├── schemas/             # Pydantic schemas
│   ├── services/
│   │   ├── user_service.py      # User CRUD + token management
│   │   ├── group_service.py     # Group CRUD
│   │   ├── permission_service.py # RBAC check_permission()
│   │   └── ...                  # agent, job, mcp_proxy, dispatcher
│   └── db/                  # Async PostgreSQL session (asyncpg)
├── dashboard/               # Next.js frontend (port 3000)
│   └── app/admin/           # Users + Groups management pages
├── alembic/                 # DB migrations (auto-applied on startup)
├── mock_mcp_server/         # Test MCP server for local dev (port 8001)
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
