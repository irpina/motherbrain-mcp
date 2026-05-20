"""Seed script for Motherbrain demo data.

Run inside the API container:
    docker compose exec api python scripts/seed_demo.py

Or via make:
    make demo

Use --force to wipe and re-seed:
    docker compose exec api python scripts/seed_demo.py --force
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import os
import random
import sys
from datetime import datetime, timezone, timedelta
from uuid import uuid4

# Need to set up the path so app imports work
sys.path.insert(0, "/app")

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.db.base import Base
from app.models.mcp_service import MCPService
from app.models.user import User
from app.models.group import Group
from app.models.user_group import UserGroup
from app.models.agent import Agent
from app.models.event_log import EventLog
from app.models.job import Job
from app.models.project_context import ProjectContext
from app.models.rule import Rule

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+asyncpg://motherbrain:motherbrain@db:5432/motherbrain")

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _minutes_ago(m: int) -> datetime:
    return _now() - timedelta(minutes=m)


# --- Real-world production gateway services ---
SERVICES = [
    {
        "service_id": "filesystem",
        "name": "Filesystem Tools",
        "endpoint": "http://api:8000",
        "capabilities": ["read_file", "write_file", "list_dir", "get_metadata"],
        "status": "online",
        "protocol": "mcp",
    },
    {
        "service_id": "github",
        "name": "GitHub API",
        "endpoint": "http://api:8000",
        "capabilities": ["list_repos", "create_issue", "get_pr", "list_commits"],
        "status": "online",
        "protocol": "rest",
    },
    {
        "service_id": "web-fetch",
        "name": "Web Fetch",
        "endpoint": "http://api:8000",
        "capabilities": ["fetch_url", "web_search", "extract_content"],
        "status": "online",
        "protocol": "mcp",
    },
    {
        "service_id": "internal-api",
        "name": "Internal API Bridge",
        "endpoint": "http://internal-api:8080",
        "capabilities": ["query_db", "send_notification"],
        "status": "offline",
        "protocol": "rest",
    },
]

AGENTS = [
    {
        "agent_id": "agent-claude-001",
        "name": "claude-cli",
        "hostname": "dev-workstation-01",
        "platform": "python-agent",
        "capabilities": {"languages": ["python", "typescript"], "shell": "zsh"},
        "status": "online",
        "token": "demo-token-claude",
    },
    {
        "agent_id": "agent-codex-002",
        "name": "codex-cli",
        "hostname": "ci-runner-03",
        "platform": "python-agent",
        "capabilities": {"languages": ["python", "go", "rust"], "shell": "bash"},
        "status": "online",
        "token": "demo-token-codex",
    },
]

GROUPS = [
    {
        "group_id": "group-eng-001",
        "name": "Engineering",
        "description": "Full access to core MCP services",
        "allowed_service_ids": ["filesystem", "github", "web-fetch"],
    },
    {
        "group_id": "group-obs-002",
        "name": "Observers",
        "description": "Read-only web access",
        "allowed_service_ids": ["web-fetch"],
    },
]

USERS = [
    {
        "user_id": "user-alice-001",
        "name": "Alice Chen",
        "email": "alice@motherbrain.local",
        "role": "admin",
        "token": "demo-token-alice",
        "group": "group-eng-001",
    },
    {
        "user_id": "user-bob-002",
        "name": "Bob Martinez",
        "email": "bob@motherbrain.local",
        "role": "user",
        "token": "demo-token-bob",
        "group": "group-eng-001",
    },
    {
        "user_id": "user-charlie-003",
        "name": "Charlie Patel",
        "email": "charlie@motherbrain.local",
        "role": "user",
        "token": "demo-token-charlie",
        "group": "group-obs-002",
    },
]

CONTEXT_ENTRIES = [
    {
        "context_key": "project-goals",
        "value": {"q3_objectives": ["Scale MCP routing to 1000 RPS", "Deploy RBAC v2", "Add agent orchestration UI"]},
        "updated_by": "Alice Chen",
        "description": "Top-level project objectives for Q3",
        "service_id": None,
        "category": "strategy",
    },
    {
        "context_key": "api-contracts",
        "value": {"version": "2.1.0", "breaking_changes": ["event_log.topic is now required"], "deprecated": ["/api/v1/events"]},
        "updated_by": "Bob Martinez",
        "description": "API versioning and contract notes",
        "service_id": "github",
        "category": "documentation",
    },
    {
        "context_key": "deployment-config",
        "value": {"region": "us-east-1", "cluster": "motherbrain-prod", "replicas": 3},
        "updated_by": "Alice Chen",
        "description": "Current production deployment topology",
        "service_id": "filesystem",
        "category": "infrastructure",
    },
]

RULES = [
    {
        "id": "rule-001",
        "text": "All MCP proxy calls must include a valid agent_id header",
        "author": "claude-cli",
        "reason": "Prevents anonymous tool calls and improves audit trails",
        "status": "active",
        "epoch": 1,
    },
    {
        "id": "rule-002",
        "text": "Never expose raw database credentials in context entries",
        "author": "codex-cli",
        "reason": "Security baseline for context sharing",
        "status": "active",
        "epoch": 1,
    },
    {
        "id": "rule-003",
        "text": "Agents should heartbeat at least every 60 seconds",
        "author": "claude-cli",
        "reason": "Keep presence data fresh for job routing",
        "status": "pending",
        "epoch": 0,
    },
]


def generate_events() -> list[dict]:
    """Generate ~80 realistic events with narrative arcs including RBAC denials.

    Topic distribution (gateway-forward):
        proxy:     ~45 events (gateway calls)
        heartbeat: ~15 events
        system:    ~10 events
        chat:      ~10 events
    """
    events = []
    agents = ["agent-claude-001", "agent-codex-002", None]
    services = ["filesystem", "github", "web-fetch", "internal-api"]
    online_services = ["filesystem", "github", "web-fetch"]

    # Real-world tools mapped to services
    service_tools = {
        "filesystem": ["read_file", "write_file", "list_dir", "get_metadata"],
        "github": ["list_repos", "create_issue", "get_pr", "list_commits"],
        "web-fetch": ["fetch_url", "web_search", "extract_content"],
        "internal-api": ["query_db", "send_notification"],
    }

    now = _now()

    # --- Batch 1: Morning proxy warm-up (events 0-19) ---
    for i in range(20):
        t = now - timedelta(minutes=180 - i * 8)
        agent = random.choice(agents)
        service = random.choice(online_services)
        tool = random.choice(service_tools[service])
        status = "ok" if random.random() > 0.12 else "error"
        events.append({
            "topic": "proxy",
            "service_id": service,
            "agent_id": agent,
            "tool_name": tool,
            "arguments": {"request_id": f"req-{i:03d}"},
            "response": {"status": status, "latency_ms": random.randint(12, 340)},
            "status": status,
            "duration_ms": random.randint(12, 340),
            "created_at": t,
        })

    # --- Batch 2: RBAC denial arc (events 20-29) ---
    # Charlie (Observers group) tries to access filesystem and gets denied
    for i in range(10):
        t = now - timedelta(minutes=90 - i * 3)
        events.append({
            "topic": "proxy",
            "service_id": "filesystem",
            "agent_id": None,
            "tool_name": "read_file",
            "arguments": {"user_id": "user-charlie-003", "path": "/etc/passwd"},
            "response": {"error": "RBAC_DENIED", "reason": "User not in allowed group for service filesystem"},
            "status": "error",
            "duration_ms": random.randint(5, 20),
            "created_at": t,
        })

    # --- Batch 3: Afternoon proxy burst (events 30-54) ---
    for i in range(25):
        t = now - timedelta(minutes=60 - i * 2)
        agent = random.choice(agents[:2])  # usually an agent
        service = random.choice(online_services)
        tool = random.choice(service_tools[service])
        status = "ok" if random.random() > 0.08 else "error"
        events.append({
            "topic": "proxy",
            "service_id": service,
            "agent_id": agent,
            "tool_name": tool,
            "arguments": {"batch": "afternoon", "idx": i},
            "response": {"ok": True, "result": f"result-{i}"} if status == "ok" else {"error": "RATE_LIMITED"},
            "status": status,
            "duration_ms": random.randint(15, 280),
            "created_at": t,
        })

    # --- Batch 4: Heartbeat burst (events 55-69) ---
    for i in range(15):
        t = now - timedelta(minutes=30 - i)
        agent = random.choice(agents[:2])
        events.append({
            "topic": "heartbeat",
            "service_id": "filesystem" if i % 2 == 0 else "web-fetch",
            "agent_id": agent,
            "tool_name": "ping",
            "arguments": {},
            "response": {"pong": True, "agent_status": "online"},
            "status": "ok",
            "duration_ms": random.randint(2, 15),
            "created_at": t,
        })

    # --- Batch 5: System events (events 70-79) ---
    system_tools = ["register_agent", "update_context", "spawn_job", "sync_rules"]
    for i in range(10):
        t = now - timedelta(minutes=10 - i * 0.8)
        status = "error" if i >= 7 else "ok"
        events.append({
            "topic": "system",
            "service_id": random.choice(online_services),
            "agent_id": random.choice(agents) if status == "ok" else None,
            "tool_name": random.choice(system_tools),
            "arguments": {"batch": "demo"},
            "response": {"error": "CONNECTION_TIMEOUT"} if status == "error" else {"ok": True},
            "status": status,
            "duration_ms": random.randint(50, 500) if status == "error" else random.randint(10, 100),
            "created_at": t,
        })

    # --- Batch 6: Chat activity (events 80-89, but we cap at 80 total) ---
    # Only add 10 chat events, trim to keep total at ~80
    chat_tools = ["send_message", "create_channel", "list_channels"]
    for i in range(10):
        t = now - timedelta(minutes=120 - i * 10)
        agent = random.choice(agents[:2])
        events.append({
            "topic": "chat",
            "service_id": "github",
            "agent_id": agent,
            "tool_name": random.choice(chat_tools),
            "arguments": {"channel": "general", "content": f"Demo message {i}"},
            "response": {"message_id": f"msg-{i:03d}", "delivered": True},
            "status": "ok",
            "duration_ms": random.randint(20, 120),
            "created_at": t,
        })

    # Sort by created_at so newest events have highest IDs (matches DB auto-increment)
    events.sort(key=lambda e: e["created_at"])

    # Take the last 80 (newest first) to match the expected ~80 count
    return events[-80:]


def generate_jobs() -> list[dict]:
    """Generate a handful of jobs in various states."""
    return [
        {
            "job_id": "job-001",
            "type": "deploy",
            "payload": {"service": "github", "version": "1.2.0"},
            "requirements": ["docker", "kubectl"],
            "status": "completed",
            "assigned_agent": "agent-claude-001",
            "created_at": _minutes_ago(180),
            "target_type": "agent",
            "result": {"deployed": True, "url": "http://github-mcp:8000"},
        },
        {
            "job_id": "job-002",
            "type": "index_files",
            "payload": {"path": "/data/docs", "recursive": True},
            "requirements": ["filesystem"],
            "status": "running",
            "assigned_agent": "agent-codex-002",
            "created_at": _minutes_ago(45),
            "target_type": "mcp",
            "target_service_id": "filesystem",
        },
        {
            "job_id": "job-003",
            "type": "security_audit",
            "payload": {"scope": "all_services"},
            "requirements": ["admin"],
            "status": "pending",
            "assigned_agent": None,
            "created_at": _minutes_ago(10),
            "target_type": "agent",
            "priority": "high",
        },
        {
            "job_id": "job-004",
            "type": "context_sync",
            "payload": {"keys": ["project-goals", "api-contracts"]},
            "requirements": [],
            "status": "failed",
            "assigned_agent": "agent-claude-001",
            "created_at": _minutes_ago(120),
            "target_type": "agent",
            "error": "Context key 'api-contracts' locked by another agent",
        },
    ]


async def is_already_seeded(db) -> bool:
    """Check if demo data already exists by looking for any seeded entity."""
    # Check for any of our hardcoded agents (most reliable — they have fixed IDs)
    result = await db.execute(
        select(Agent).where(Agent.agent_id == "agent-claude-001")
    )
    return result.scalar_one_or_none() is not None


async def seed():
    async with AsyncSessionLocal() as db:
        # --- MCP Services ---
        for svc in SERVICES:
            db.add(MCPService(**svc))
        print(f"  + {len(SERVICES)} MCP services")

        # --- Groups ---
        for g in GROUPS:
            db.add(Group(**g))
        print(f"  + {len(GROUPS)} groups")

        # --- Users ---
        user_groups = []
        for u in USERS:
            user_groups.append((u["user_id"], u["group"]))
            db.add(User(
                user_id=u["user_id"],
                name=u["name"],
                email=u["email"],
                role=u["role"],
                token_hash=_hash_token(u["token"]),
            ))
        print(f"  + {len(USERS)} users")

        # --- User-Group links ---
        for user_id, group_id in user_groups:
            db.add(UserGroup(user_id=user_id, group_id=group_id))
        print(f"  + {len(USERS)} user-group links")

        # --- Agents ---
        for a in AGENTS:
            token = a.pop("token")
            db.add(Agent(
                **a,
                token_hash=_hash_token(token),
                last_heartbeat=_now(),
            ))
        print(f"  + {len(AGENTS)} agents")

        # --- Context entries ---
        for ctx in CONTEXT_ENTRIES:
            db.add(ProjectContext(**ctx))
        print(f"  + {len(CONTEXT_ENTRIES)} context entries")

        # --- Rules ---
        for r in RULES:
            db.add(Rule(**r))
        print(f"  + {len(RULES)} rules")

        # --- Jobs ---
        for j in generate_jobs():
            db.add(Job(**j))
        print(f"  + {len(generate_jobs())} jobs")

        # --- Events ---
        events = generate_events()
        for e in events:
            db.add(EventLog(**e))
        print(f"  + {len(events)} events")

        await db.commit()
        print("\nDemo data seeded successfully.")


async def clear_existing():
    """Remove existing demo data to avoid duplicates on re-runs."""
    async with AsyncSessionLocal() as db:
        from sqlalchemy import delete
        await db.execute(delete(EventLog))
        await db.execute(delete(Job))
        await db.execute(delete(Rule))
        await db.execute(delete(ProjectContext))
        await db.execute(delete(Agent))
        await db.execute(delete(UserGroup))
        await db.execute(delete(User))
        await db.execute(delete(Group))
        await db.execute(delete(MCPService))
        await db.commit()
        print("Cleared existing demo data.")


async def main():
    parser = argparse.ArgumentParser(description="Seed Motherbrain demo data")
    parser.add_argument("--force", action="store_true", help="Wipe existing data before seeding")
    args = parser.parse_args()

    print("Motherbrain Demo Seeder")
    print("=" * 40)

    async with AsyncSessionLocal() as db:
        if await is_already_seeded(db):
            if args.force:
                print("Demo data already present. --force flag set, clearing...")
                await clear_existing()
            else:
                print("Demo data already present. Run with --force to re-seed, or `make clean && make up` to reset.")
                return

    await seed()


if __name__ == "__main__":
    asyncio.run(main())
