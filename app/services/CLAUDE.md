# Services — Business Logic Layer

## Purpose
Contains all business logic. Services are the heart of the application.

## Structure

```
services/
├── agent_service.py        # Agent CRUD, token management
├── job_service.py          # Job lifecycle, assignment
├── agent_action_service.py # Audit logging
├── project_context_service.py  # KV store operations
├── agent_message_service.py    # Message handling
├── scheduler.py            # Job-to-agent matching
├── router.py               # NEW: Route jobs to agents or MCP
└── mcp_proxy.py            # NEW: Call MCP services
```

## Service Rules

### 1. Function Signature Pattern

```python
async def do_something(
    db: AsyncSession,      # Always first
    entity_id: str,        # Then identifiers
    data: SomeSchema,      # Then data models
    **kwargs               # Optional params last
) -> ReturnType:
```

### 2. Database Operations

Always use `await db.commit()` after changes:

```python
async def update_status(db: AsyncSession, job_id: str, status: str):
    job = await get_job(db, job_id)
    if not job:
        raise ValueError(f"Job {job_id} not found")
    
    job.status = status
    await db.commit()      # Don't forget!
    await db.refresh(job)  # Refresh to get updated fields
    return job
```

### 3. Return Values

- Return ORM models (routes convert to schemas)
- Return `None` for "not found" (let routes handle 404)
- Return `bool` for success/failure operations

### 4. Error Handling

- Raise exceptions for error conditions
- Use specific exception types when possible
- Document expected exceptions in docstrings

```python
class NoAgentAvailable(Exception):
    pass

async def assign_job(db: AsyncSession, job_id: str):
    job = await get_job(db, job_id)
    agents = await list_online_agents(db)
    
    agent = match_job_to_agent(job, agents)
    if not agent:
        raise NoAgentAvailable(f"No agent for job {job_id}")
    
    # ... assign and return
```

## Adding a New Service

1. Create `app/services/my_service.py`
2. Export from `app/services/__init__.py`
3. Import in routes that need it

## Extension Points

**Safe to extend:**
- Add new matching algorithms in `scheduler.py`
- Add new routing logic in `router.py`
- Add new proxy methods in `mcp_proxy.py`

**Stub functions** (marked with `# TODO: Implement`):
- Retry logic in `mcp_proxy.py`
- Load balancing in `router.py`
- Topic-based routing (future)

## Testing Services

Services can be tested independently:

```python
async def test_job_service():
    async with AsyncSession(engine) as db:
        job = await job_service.create_job(db, JobCreate(...))
        assert job.status == "pending"
```
