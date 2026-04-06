# Motherbrain MCP

A complete Python project scaffold for the **Motherbrain MCP control plane** using FastAPI, PostgreSQL, Redis, and Docker Compose.

## Features

- **FastAPI** - Modern, fast web framework for building APIs
- **PostgreSQL** - Relational database with SQLAlchemy 2.0 async ORM
- **Redis** - Job queue and pub/sub for real-time events
- **Docker Compose** - Complete local development environment
- **Agent SDK** - Example agent implementation with token-based auth
- **Hierarchical Jobs** - Parent/child relationships and dependencies
- **Audit Logging** - Track all agent actions
- **Shared Context** - Key-value store for project-wide state
- **Inter-Agent Messaging** - Communication between agents

## Architecture

```
motherbrain-mcp/
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── core/                # Configuration, security, dependencies
│   ├── api/routes/          # REST API endpoints
│   │   ├── agents.py        # Agent registration, heartbeat, actions
│   │   ├── jobs.py          # Job CRUD, queue, status updates
│   │   ├── context.py       # Shared project context (KV store)
│   │   ├── messages.py      # Inter-agent messaging
│   │   └── actions.py       # Audit log queries
│   ├── models/              # SQLAlchemy models
│   │   ├── agent.py         # Agent model with token auth
│   │   ├── job.py           # Job with hierarchy (parent/child/depends_on)
│   │   ├── agent_action.py  # Audit log
│   │   ├── project_context.py
│   │   └── agent_message.py
│   ├── schemas/             # Pydantic schemas
│   ├── services/            # Business logic
│   ├── db/                  # Database setup
│   └── queue/               # Redis queue operations
├── agent/                   # Example agent implementation
├── docker-compose.yml       # Services orchestration
├── Dockerfile               # API container
├── Makefile                 # Common commands
├── requirements.txt         # Python dependencies
└── .env.example             # Environment variables
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for running agent outside Docker)
- Make (optional, for convenience commands)

### Run with Docker Compose

1. Clone this repository and navigate to the project:
```bash
cd motherbrain-mcp
```

2. Create environment file:
```bash
cp .env.example .env
```

3. Start all services:
```bash
make up
# Or: docker compose up --build -d
```

4. Verify the API is running:
```bash
curl http://localhost:8000/health
```

5. Access the API documentation:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Run the Example Agent

First, register an agent to get a token:

```bash
curl -X POST http://localhost:8000/agents/register \
  -H "Content-Type: application/json" \
  -H "X-API-Key: supersecret" \
  -d '{"platform": "python-agent", "capabilities": {"python": true}}'
# Save the returned token!
```

Then run the agent with the token:

```bash
export AGENT_TOKEN="your-token-here"
make agent
# Or: cd agent && python agent.py
```

Or register a new agent automatically:
```bash
make agent
# The agent will register itself and display the token
```

## API Usage Examples

### Authentication

Two levels of authentication:

1. **Master API Key** (`X-API-Key` header) - For admin operations (creating jobs, listing agents, etc.)
2. **Agent Token** (`X-Agent-Token` header) - For agent operations (heartbeat, claiming jobs, updating status)

### Agents

**Register an Agent (Admin)**
```bash
curl -X POST http://localhost:8000/agents/register \
  -H "Content-Type: application/json" \
  -H "X-API-Key: supersecret" \
  -d '{
    "platform": "python-agent",
    "capabilities": {"python": true, "shell": true}
  }'
```

**Send Heartbeat (Agent)**
```bash
curl -X POST http://localhost:8000/agents/heartbeat \
  -H "X-Agent-Token: YOUR_AGENT_TOKEN"
```

**List Agents (Admin)**
```bash
curl http://localhost:8000/agents/ \
  -H "X-API-Key: supersecret"
```

**Get Agent Actions (Audit Log)**
```bash
curl "http://localhost:8000/agents/AGENT_ID/actions?limit=50" \
  -H "X-API-Key: supersecret"
```

### Jobs

**Create a Job (Admin)**
```bash
curl -X POST http://localhost:8000/jobs/ \
  -H "Content-Type: application/json" \
  -H "X-API-Key: supersecret" \
  -d '{
    "type": "echo",
    "payload": {"message": "Hello World"},
    "requirements": ["python"],
    "priority": "high",
    "depends_on": []
  }'
```

**Get Next Job (Agent)**
```bash
curl http://localhost:8000/jobs/next \
  -H "X-Agent-Token: YOUR_AGENT_TOKEN"
```

**Update Job Status (Agent)**
```bash
curl -X POST http://localhost:8000/jobs/JOB_ID/status \
  -H "Content-Type: application/json" \
  -H "X-Agent-Token: YOUR_AGENT_TOKEN" \
  -d '{
    "status": "completed",
    "log": "Job finished successfully"
  }'
```

**Add Job Note (Admin)**
```bash
curl -X POST http://localhost:8000/jobs/JOB_ID/notes \
  -H "Content-Type: application/json" \
  -H "X-API-Key: supersecret" \
  -d '{
    "author": "admin",
    "content": "This job is critical"
  }'
```

### Project Context

**Set Context Value (Admin)**
```bash
curl -X POST http://localhost:8000/context/my-key \
  -H "Content-Type: application/json" \
  -H "X-API-Key: supersecret" \
  -d '{
    "value": {"important": "data"},
    "updated_by": "admin",
    "description": "Important configuration"
  }'
```

**Get Context Value (Admin)**
```bash
curl http://localhost:8000/context/my-key \
  -H "X-API-Key: supersecret"
```

**List All Context Keys (Admin)**
```bash
curl http://localhost:8000/context/ \
  -H "X-API-Key: supersecret"
```

### Agent Messages

**Send Message (Admin)**
```bash
curl -X POST http://localhost:8000/messages/ \
  -H "Content-Type: application/json" \
  -H "X-API-Key: supersecret" \
  -d '{
    "sender_id": "AGENT_1",
    "recipient_id": "AGENT_2",
    "content": "Hello from agent 1!",
    "message_type": "text",
    "priority": "normal"
  }'
```

**Check Inbox (Agent)**
```bash
curl "http://localhost:8000/messages/inbox?unread_only=true" \
  -H "X-Agent-Token: YOUR_AGENT_TOKEN"
```

**Mark Message Read (Agent)**
```bash
curl -X POST http://localhost:8000/messages/MESSAGE_ID/read \
  -H "X-Agent-Token: YOUR_AGENT_TOKEN"
```

### Actions (Audit Log)

**List All Actions (Admin)**
```bash
curl "http://localhost:8000/actions/?limit=100" \
  -H "X-API-Key: supersecret"
```

**Get Actions by Job**
```bash
curl "http://localhost:8000/actions/job/JOB_ID" \
  -H "X-API-Key: supersecret"
```

## Development

### Makefile Commands

```bash
make up       # Start all services
make down     # Stop all services
make logs     # Follow logs
make shell    # Open shell in API container
make agent    # Run example agent
make clean    # Stop and remove volumes
```

### Local Development (without Docker)

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Start PostgreSQL and Redis locally

4. Update `.env` for local development:
```bash
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/motherbrain
REDIS_URL=redis://localhost:6379
API_KEY=supersecret
```

5. Run the API:
```bash
uvicorn app.main:app --reload
```

### Running on Proxmox (Ubuntu + Docker)

The same `docker-compose.yml` works on Proxmox:

1. Copy the project to your Ubuntu server
2. Create `.env` file
3. Run `docker compose up -d`

Additional steps for Proxmox:

```bash
# Allow API port through firewall
sudo ufw allow 8000

# Services will auto-restart on reboot (restart: unless-stopped)
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection URL | `postgresql+asyncpg://postgres:postgres@db:5432/motherbrain` |
| `REDIS_URL` | Redis connection URL | `redis://redis:6379` |
| `API_KEY` | Master API key for admin access | `supersecret` |
| `AGENT_TOKEN` | Agent token (for running agent) | None |

## API Endpoints Reference

### Agents
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/agents/register` | API Key | Register a new agent |
| POST | `/agents/heartbeat` | Agent Token | Update agent heartbeat |
| GET | `/agents/` | API Key | List all agents |
| GET | `/agents/{id}` | API Key | Get agent details |
| GET | `/agents/{id}/actions` | API Key | Get agent audit log |
| POST | `/agents/{id}/status` | API Key | Update agent status |

### Jobs
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/jobs/` | API Key | Create a new job |
| GET | `/jobs/next` | Agent Token | Get next available job |
| GET | `/jobs/{id}` | API Key | Get job by ID |
| POST | `/jobs/{id}/status` | Agent Token | Update job status |
| POST | `/jobs/{id}/logs` | Agent Token | Append job logs |
| POST | `/jobs/{id}/notes` | API Key | Add job note |
| POST | `/jobs/{id}/child/{child_id}` | API Key | Link child job |

### Context
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/context/` | API Key | List all context keys |
| GET | `/context/{key}` | API Key | Get context value |
| POST | `/context/{key}` | API Key | Create/update context |
| PUT | `/context/{key}` | API Key | Update context |
| DELETE | `/context/{key}` | API Key | Delete context |

### Messages
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/messages/` | API Key | Send message |
| GET | `/messages/inbox` | Agent Token | Get inbox |
| GET | `/messages/sent` | Agent Token | Get sent messages |
| GET | `/messages/{id}` | Agent Token | Get specific message |
| POST | `/messages/{id}/read` | Agent Token | Mark as read |

### Actions (Audit Log)
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/actions/` | API Key | List all actions |
| GET | `/actions/agent/{id}` | API Key | Actions by agent |
| GET | `/actions/job/{id}` | API Key | Actions by job |

## Data Model

### Job Hierarchy

Jobs support parent/child relationships and dependencies:

```python
{
  "job_id": "uuid",
  "type": "echo",
  "parent_job": "parent-uuid",      # Optional parent job
  "child_jobs": ["child-uuid"],     # List of child job IDs
  "depends_on": ["other-job"],      # Jobs that must complete first
  "priority": "high",               # low/medium/high
  "notes": [...]                    # Timestamped notes
}
```

### Audit Log

All significant actions are logged:

- `registered` - Agent registration
- `heartbeat` - Agent heartbeat
- `claimed_job` - Agent took a job from queue
- `completed_job` - Job finished successfully
- `failed_job` - Job failed

## Architecture Decisions

1. **Async throughout** - FastAPI with async SQLAlchemy (asyncpg) for non-blocking I/O
2. **Token-based auth** - Each agent gets a unique token on registration
3. **Redis patterns** - Separate List for job queue (RPUSH/LPOP) and Pub/Sub for events
4. **Server-side UUIDs** - Agent and job IDs generated by the server
5. **Hierarchical jobs** - Support for parent/child relationships and dependencies
6. **Audit logging** - All agent actions tracked for debugging and compliance

## Comparison with Agent-MCP

| Feature | Agent-MCP | Motherbrain |
|---------|-----------|-------------|
| Transport | MCP stdio/SSE | REST API |
| Database | SQLite | PostgreSQL |
| Auth | Per-agent token | Per-agent token + Master API key |
| Job Model | Hierarchical | Hierarchical |
| Queue | SQLite write-queue | Redis |
| Audit Log | `agent_actions` table | `agent_actions` table |
| Shared Memory | `project_context` table | `project_context` table |
| Messaging | `agent_messages` table | `agent_messages` table |
| Docker | Not included | Full compose setup |
| Dashboard | Next.js | Future stretch goal |

## Stretch Goals

- [ ] WebSocket support for real-time updates
- [ ] Job scheduling with cron expressions
- [ ] RAG/search with vector embeddings
- [ ] File tracking and content hashing
- [ ] Next.js dashboard
- [ ] Job cancellation and timeout handling
- [ ] Retry logic with exponential backoff
- [ ] Structured logging with correlation IDs
- [ ] Alembic migrations

## License

MIT
