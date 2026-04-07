# App Module — FastAPI Application

## Purpose
This is the core FastAPI application. Everything here is runtime code.

## Structure

```
app/
├── main.py          # App entry point, lifespan events, CORS
├── mcp_server.py    # FastMCP server mounted at /mcp
├── api/             # HTTP routes (IMPORT-ONLY, no logic)
├── background/      # heartbeat.py + health_check.py background tasks
├── core/            # Config, security constants
├── db/              # Database connection management
├── models/          # SQLAlchemy ORM models
├── schemas/         # Pydantic validation models
├── services/        # Business logic (where the work happens)
└── queue/           # Redis queue abstraction
```

## Key Rules

### 1. Routes Layer (`api/`)
- **ONLY** HTTP concerns: routing, auth headers, status codes
- **NEVER** put business logic here
- **ALWAYS** delegate to services
- Use `Depends()` for dependencies

```python
# GOOD: Route delegates to service
@router.post("/jobs")
async def create_job(data: JobCreate, db: Depends(get_db)):
    return await job_service.create_job(db, data)

# BAD: Business logic in route
@router.post("/jobs")
async def create_job(data: JobCreate, db: Depends(get_db)):
    # Don't do this here!
    job = Job(**data.model_dump())
    db.add(job)
    await db.commit()
```

### 2. Services Layer (`services/`)
- **ALL** business logic lives here
- Services receive `AsyncSession` as parameter
- Services are pure Python, no HTTP concerns
- Services can call other services

### 3. Models Layer (`models/`)
- SQLAlchemy 2.0 style with `Mapped[]`
- Default values use `default=lambda: ...`
- Foreign keys are strings (UUIDs), not objects

### 4. Schemas Layer (`schemas/`)
- Pydantic v2 with `ConfigDict(from_attributes=True)`
- Separate Create/Update/Response models
- Use `Optional[]` for nullable fields

## Adding a New Feature

1. Model → `app/models/feature.py`
2. Schema → `app/schemas/feature.py`
3. Service → `app/services/feature_service.py`
4. Route → `app/api/routes/feature.py`
5. Register route in `main.py`
6. Create Alembic migration

## Safe to Modify

- Add new services
- Add new routes
- Add new models
- Extend existing schemas
- Add helper functions

## Do Not Modify

- `db/base.py` — keep as simple DeclarativeBase
- `core/config.py` — only add env vars
- Existing model primary keys
- Existing column types (create migrations instead)
