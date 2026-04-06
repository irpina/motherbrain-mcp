# Models — SQLAlchemy ORM

## Purpose
Define database tables using SQLAlchemy 2.0 declarative syntax.

## Structure

```
models/
├── agent.py              # Agent registration and state
├── job.py                # Job/task definitions
├── agent_action.py       # Audit log entries
├── project_context.py    # Shared KV store
├── agent_message.py      # Inter-agent messages
├── mcp_service.py        # NEW: MCP service registry
└── __init__.py           # Export all models
```

## SQLAlchemy 2.0 Style

### Column Definitions

```python
from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class MyModel(Base):
    __tablename__ = "my_models"
    
    # Primary key with UUID
    id: Mapped[str] = mapped_column(
        String, 
        primary_key=True, 
        default=lambda: str(uuid4())
    )
    
    # Required field
    name: Mapped[str] = mapped_column(String, nullable=False)
    
    # Optional field
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    # JSON field
    data: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # List field (stored as JSON)
    tags: Mapped[list] = mapped_column(JSON, default=list)
    
    # Timestamp with timezone
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
```

## Important Patterns

### 1. Always Use `Mapped[Type]`

```python
# GOOD
name: Mapped[str] = mapped_column(String)

# BAD (SQLAlchemy 1.x style)
name = Column(String)
```

### 2. Default Values

```python
# For mutable defaults (list, dict), use default= not default_factory
# SQLAlchemy handles this correctly
tags: Mapped[list] = mapped_column(JSON, default=list)

# For UUIDs
default=lambda: str(uuid4())

# For timestamps
default=lambda: datetime.now(timezone.utc)
```

### 3. Foreign Keys

We use string IDs (UUIDs) for flexibility:

```python
parent_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
# Not: parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("parents.id"))
```

### 4. Adding a New Model

1. Create file: `app/models/my_model.py`
2. Define class extending `Base`
3. Add to `app/models/__init__.py`:
   ```python
   from app.models.my_model import MyModel
   __all__ = [..., "MyModel"]
   ```
4. Create Alembic migration
5. Run `alembic upgrade head`

## Migrations Required For

- New tables
- New columns
- Column type changes
- Index additions
- Constraint changes

**Never** modify existing columns directly — always create a migration!
