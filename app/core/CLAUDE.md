# Core — Configuration and Security

## Purpose
Application-wide configuration, settings, and security utilities.

## Structure

```
core/
├── config.py      # Pydantic settings from environment
├── security.py    # Auth utilities (if needed)
└── CLAUDE.md      # This file
```

## Configuration (`config.py`)

Uses Pydantic v2 `BaseSettings` for env var loading:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    API_KEY: str
    
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
```

### Adding New Config

1. Add field to `Settings` class with type
2. Add to `.env.example`
3. Document in README.md

```python
class Settings(BaseSettings):
    # ... existing ...
    NEW_SETTING: str = "default_value"  # Add default or make required
```

## Security (`security.py`)

Currently minimal — auth is handled in `api/deps.py`:

- `verify_api_key()` — admin API key validation
- `get_current_agent()` — agent token validation

### API Key Storage

- Master API key: single env var (`API_KEY`)
- Agent tokens: generated at registration, stored in DB
- MCP service keys: hashed with SHA-256, stored in `mcp_services.api_key_hash`

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `REDIS_URL` | Yes | Redis connection string |
| `API_KEY` | Yes | Master admin API key |

For Docker, these are in `.env` file and loaded via `env_file` in compose.

## Modification Guidelines

**Safe:**
- Add new config settings with defaults
- Add security utilities
- Add constants/enums

**Avoid:**
- Hardcoding secrets
- Complex initialization logic (use `main.py` lifespan)
- Circular imports
