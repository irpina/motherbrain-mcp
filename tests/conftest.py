"""Pytest fixtures for integration testing.

This module provides shared fixtures for database sessions and HTTP clients
that all tests can use. It sets up an in-memory SQLite database for fast,
isolated tests without requiring PostgreSQL.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.db.base import Base
from app.db.session import get_db

# Use SQLite in-memory for tests — no external DB required
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="function")
async def db_session():
    """Create a fresh database session for each test.
    
    Yields:
        AsyncSession: Database session with all tables created
    """
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    """FastAPI test client with DB session overridden to use test DB.
    
    This fixture creates an HTTP client that talks to the FastAPI app
    with the database session replaced by our test session.
    
    Args:
        db_session: The test database session fixture
    
    Yields:
        AsyncClient: HTTP client with base URL and API key header
    """
    app.dependency_overrides[get_db] = lambda: db_session
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"X-API-Key": "supersecret"}
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def admin_client(client):
    """Client with admin API key pre-configured.
    
    This is an alias for the base client since it already has the API key.
    Use this when you want to be explicit about admin-level operations.
    """
    return client
