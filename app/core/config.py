from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str  # postgresql+asyncpg://user:pass@db:5432/motherbrain
    REDIS_URL: str     # redis://redis:6379
    API_KEY: str
    
    # Optional: Agent configuration (used by agent/agent.py, not core API)
    API_URL: str = "http://localhost:8000"
    PLATFORM: str = "python-agent"
    CAPABILITIES: str = '["python"]'

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
