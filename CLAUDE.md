# Motherbrain MCP — Agent Development Guide

> **Purpose**: Central control plane and message router for AI agents and MCP services.

## Project Overview

Motherbrain MCP is a FastAPI-based control plane that:
- Exposes a unified MCP endpoint for LLM clients
- Proxies tool calls to registered MCP services
- Logs all activity to a persistent event log
- Auto-monitors service health every 30s
- Registers and manages AI agents
- Routes jobs to agents or MCP services
- Tracks execution via audit logs
- Provides inter-agent messaging
- Manages shared project context

## Architecture

```
motherbrain-mcp/
├── app/                     # FastAPI application
│   ├── mcp_server.py        # FastMCP server — 7 MCP tools
│   ├── api/                 # HTTP routes (thin layer, no business logic)
│   ├── background/          # Heartbeat + health-check background tasks
│   ├── core/                # Configuration and security
│   ├── db/                  # Database models and sessions
│   ├── models/              # SQLAlchemy ORM models
│   │   └── event_log.py     # Unified activity log model
│   ├── schemas/             # Pydantic request/response models
│   ├── services/            # Business logic and orchestration
│   └── queue/               # Redis queue operations
├── agent/                   # Example agent implementation
├── dashboard/               # Next.js frontend
├── alembic/                 # Database migrations
└── mock_mcp_server/         # Test MCP server (see below)
```

## Key Principles

1. **Separation of Concerns**
   - Routes handle HTTP only
   - Services contain all business logic
   - Models define data structures

2. **Async Throughout**
   - All database operations are async
   - All service methods are async
   - Use `asyncpg` for PostgreSQL

3. **Type Safety**
   - Use Pydantic v2 for all schemas
   - Use SQLAlchemy 2.0 `Mapped[]` syntax
   - Always include type hints

## Extension Points

When adding new features:

1. **New API endpoint?** → Add to `app/api/routes/`
2. **New business logic?** → Add to `app/services/`
3. **New data model?** → Add to `app/models/` + create Alembic migration
4. **New schema?** → Add to `app/schemas/`

## Running Locally

```bash
# Start all services
cp .env.example .env
make up

# View logs
make logs

# Access API
curl http://localhost:8000/health

# Access Dashboard
open http://localhost:3000
```

## Testing

Use the mock MCP server for testing routing without external dependencies:
```bash
cd mock_mcp_server
python main.py  # Runs on port 8001
```

## Database Migrations

```bash
# Create new migration
alembic revision -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```
