# API Routes — HTTP Interface Layer

## Purpose
Thin HTTP layer that validates requests and delegates to services.

## Structure

```
api/
├── deps.py          # FastAPI dependencies (auth, DB sessions)
└── routes/
    ├── agents.py    # Agent registration, heartbeat, status
    ├── jobs.py      # Job CRUD, claiming, status updates
    ├── context.py   # Project context (KV store)
    ├── messages.py  # Inter-agent messaging
    ├── actions.py   # Audit log queries
    └── mcp.py       # MCP service registry (NEW)
```

## Route Rules

### 1. Import Order Matters
FastAPI matches routes in order. Define specific routes BEFORE parameter routes:

```python
# GOOD: Specific routes first
@router.get("/jobs/")           # List all jobs
@router.get("/jobs/next")       # Get next available job
@router.get("/jobs/{job_id}")   # Get specific job

# BAD: Would never match /jobs/next
@router.get("/jobs/{job_id}")   # This catches "next" as job_id!
@router.get("/jobs/next")
```

### 2. Auth Patterns

**Admin operations** (create jobs, list all agents):
```python
async def create_job(..., _: str = Depends(verify_api_key)):
```

**Agent operations** (claim job, heartbeat):
```python
async def claim_job(..., agent: Agent = Depends(get_current_agent)):
```

### 3. HTTP Status Codes

| Situation | Return |
|-----------|--------|
| Success with data | Return model directly (200) |
| Success no content | `Response(status_code=204)` |
| Not found | `raise HTTPException(404, ...)` |
| Forbidden | `raise HTTPException(403, ...)` |
| Validation | Let Pydantic handle (422) |

### 4. Request Body Models

**NEVER** use bare types for POST bodies:

```python
# BAD: Query param, not body
async def update_status(status: str): ...

# GOOD: Explicit body model
class StatusUpdate(BaseModel):
    status: str

async def update_status(update: StatusUpdate): ...
```

## Adding a New Route

1. Create `app/api/routes/new_feature.py`
2. Import in `app/main.py` and include with `app.include_router()`
3. Add to Swagger docs at `/docs`

## Example Route File Template

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import verify_api_key, get_db
from app.schemas.new_feature import NewFeatureCreate, NewFeatureResponse
from app.services import new_feature_service

router = APIRouter(prefix="/new-feature", tags=["new-feature"])

@router.post("/", response_model=NewFeatureResponse)
async def create(
    data: NewFeatureCreate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key)
):
    return await new_feature_service.create(db, data)
```
