"""Motherbrain MCP Server — Meta-tools for proxying to registered MCP services.

This FastMCP server exposes tools that let LLMs discover, manage, and call
any registered MCP service through Motherbrain:

Discovery & Management:
- discover() — Live orientation to the system
- get_system_state() — Full system state as JSON
- list_tools(service_id) — List tools on a specific service
- register_service(...) — Register or update an MCP service
- remove_service(service_id) — Unregister a service

Job Dispatch:
- create_job(type, payload, ...) — Dispatch work to registered agents
- get_job_status(job_id) — Check progress and results

Proxy & Context:
- call_tool(service_id, tool_name, arguments) — Route calls to target MCP
- get_event_log(...) — Read the unified activity log
- get_context(key) — Fetch from shared context/skill store
- set_context(key, value_json, ...) — Store in shared context

The LLM connects to Motherbrain (port 8000/mcp) and can access ALL
registered MCP services through a single endpoint.
"""

import json
import time
from datetime import datetime, timezone, timedelta
from types import SimpleNamespace
from mcp.server.fastmcp import FastMCP, Context

from app.db.session import AsyncSessionLocal
from app.services.system_state import get_system_state as _get_system_state
from app.services import mcp_service_service, mcp_proxy
from app.services.event_log import append_event, get_events
from app.services.agent_registry import agent_registry
from app.background.health_check import _probe
from app.schemas.mcp_service import MCPServiceCreate, MCPServiceUpdate
from app.services.job_service import create_job as _create_job, get_job
from app.schemas.job import JobCreate
from app.middleware.mcp_auth import get_current_user_token
from app.queue import redis_queue


async def _get_db():
    """Get a database session."""
    async with AsyncSessionLocal() as session:
        return session


def _get_caller_name(ctx: Context) -> str | None:
    """Extract the calling client's name from the MCP initialize handshake.
    
    This reads clientInfo.name from the initialize request that established
    the current MCP session. Returns None if not available.
    """
    try:
        params = ctx.request_context.session.client_params
        if params and params.clientInfo:
            return params.clientInfo.name
    except Exception:
        pass
    return None


def _infer_topic(service_id: str, tool_name: str) -> str:
    """Infer the event topic from service_id and tool_name."""
    if "agentchattr" in service_id or tool_name.startswith("chat_"):
        return "chat"
    return "proxy"


async def _discover_capabilities(endpoint: str) -> list[str]:
    """Call tools/list on an MCP endpoint and return tool names.
    
    Uses the same MCP session handshake as mcp_proxy._call_mcp_native.
    Returns empty list on any failure — callers must treat this as best-effort.
    """
    from urllib.parse import urlparse
    from uuid import uuid4
    import httpx

    mcp_url = endpoint.rstrip("/") + "/mcp"
    parsed = urlparse(endpoint)
    port_str = f":{parsed.port}" if parsed.port else ""
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "Host": f"localhost{port_str}",
    }

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            # Step 1: initialize
            init_resp = await client.post(mcp_url, headers=headers, json={
                "jsonrpc": "2.0",
                "id": str(uuid4()),
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {},
                    "clientInfo": {"name": "motherbrain", "version": "1.0"}
                }
            })
            init_resp.raise_for_status()
            session_id = init_resp.headers.get("mcp-session-id")
            session_headers = {**headers}
            if session_id:
                session_headers["mcp-session-id"] = session_id

            # Step 2: initialized notification
            await client.post(mcp_url, headers=session_headers, json={
                "jsonrpc": "2.0",
                "method": "notifications/initialized"
            })

            # Step 3: tools/list
            list_resp = await client.post(mcp_url, headers=session_headers, json={
                "jsonrpc": "2.0",
                "id": str(uuid4()),
                "method": "tools/list",
                "params": {}
            })
            list_resp.raise_for_status()
            
            # Parse SSE or plain JSON (same as mcp_proxy._parse_mcp_response_body)
            content_type = list_resp.headers.get("content-type", "")
            if "text/event-stream" in content_type:
                data = None
                for line in list_resp.text.splitlines():
                    if line.startswith("data:"):
                        payload = line[len("data:"):].strip()
                        if payload:
                            data = json.loads(payload)
                            break
            else:
                data = list_resp.json()

            if not data:
                return []

            tools = data.get("result", {}).get("tools", [])
            return [t["name"] for t in tools if "name" in t]

    except Exception:
        return []


# Create FastMCP server
mcp = FastMCP(
    "motherbrain",
    streamable_http_path="/",  # Mount at root so FastAPI prefix works
    instructions=(
        "# Welcome to Motherbrain\n\n"
        "Motherbrain is a coordination hub for AI agents and humans. "
        "It connects services, routes jobs, and logs all activity in one place.\n\n"
        "## Startup sequence (do this when you first connect)\n\n"
        "1. Call `discover()` — get a live orientation: what services are online, "
        "who's here, and the full how-to guide.\n\n"
        "2. Register your heartbeat loop — POST to "
        "`http://localhost:8000/api/heartbeat/{your_name}` every 30 seconds.\n"
        "   - This keeps you visible as online and delivers any triggers (messages addressed to you).\n"
        "   - If you have a DB agent_id (from POST /agents/register), append "
        "`?agent_id={your_id}` so the Agents panel stays current.\n\n"
        "3. On each heartbeat response, check `triggers` — these are jobs or messages "
        "sent directly to you. Process each one and respond via chat.\n\n"
        "4. Communicate using `call_tool('agentchattr-mcp', 'chat_send', "
        "{sender, channel, message, choices})` — always use channel `motherbrain`.\n\n"
        "5. After any action, call `get_event_log()` to see what happened and "
        "decide your next step.\n\n"
        "## Key tools\n"
        "- `discover()` — full live orientation\n"
        "- `get_event_log(topic, service_id)` — unified activity log\n"
        "- `call_tool(service_id, tool_name, arguments)` — invoke any connected service\n"
        "- `get_context('skills.name')` — fetch a reusable skill/prompt\n"
        "- `get_system_state()` — raw JSON system state\n\n"
        "Start with `discover()` to see what's live right now.\n\n"
        "For the full operating manual, call `get_context('skills.guide')`."
    ),
)


@mcp.tool()
async def discover(ctx: Context) -> str:
    """What is Motherbrain and how do I use it?
    
    Returns a plain-language orientation explaining the system,
    what's currently online, who's here, and how to pilot Motherbrain.
    Call this first when connecting to understand the ecosystem.
    """
    start_time = time.time()
    db = await _get_db()
    
    try:
        # Get current services
        services = await mcp_service_service.list_services(db)
        
        # Build services section
        services_lines = []
        for svc in services:
            status_emoji = "🟢" if svc.status == "online" else "🔴"
            caps = ", ".join(svc.capabilities or [])
            services_lines.append(f"- {status_emoji} {svc.name} — {caps}")
        
        if not services_lines:
            services_lines.append("- (no services registered)")
        
        # Build agents section from registry
        agents_lines = []
        now = datetime.now(timezone.utc)
        for name, last_seen in agent_registry.items():
            age = (now - last_seen).total_seconds()
            if age < 300:
                agents_lines.append(f"- 🟢 {name} (online, last seen {int(age)}s ago)")
            else:
                agents_lines.append(f"- 🟡 {name} (away, last seen {int(age)}s ago)")
        
        if not agents_lines:
            agents_lines.append("- (no agents registered)")
        
        result = f"""# Motherbrain

Motherbrain is a coordination hub for AI agents and humans. It connects
services, routes messages, and tracks activity across a multi-agent session.

## What's online right now
{chr(10).join(services_lines)}

## Who's here
{chr(10).join(agents_lines)}

## How to pilot Motherbrain

1. **Stay registered** — POST /api/heartbeat/{{your_name}} every 30s.
   Your triggers (messages addressed to you) are delivered on each heartbeat.

2. **Communicate** — use call_tool to invoke agentchattr tools (chat_send, chat_read)
   to talk to humans and other agents in #motherbrain.

3. **Invoke services** — use call_tool(service_id, tool_name, args)
   to use any registered service's capabilities.

4. **Read the log** — Motherbrain logs every tool call as an event.
   After calling a tool, use get_event_log() to see results and decide next actions.

5. **Filter the log** — use topic="chat" for chat events, topic="heartbeat" for check-ins,
   or service_id="agentchattr-mcp" to filter by source.

6. **Inspect the ecosystem** — get_system_state() for raw state,
   list_tools(service_id) to see what a service can do.

7. **Skill store** — context entries under skills.* are reusable agent skills.
   get_context("skills.summarize") to fetch a skill prompt.
   set_context("skills.my_skill", '{{"prompt": "..."}}', "description") to store one.
   Browse all skills at http://localhost:3000/context.

## Full operating manual
Call `get_context("skills.guide")` for the complete guide:
startup sequence, tool reference, registered services, agent identity,
communication patterns, and tips.
"""
        # Log this system call
        duration_ms = int((time.time() - start_time) * 1000)
        await append_event(
            topic="system",
            service_id="motherbrain",
            tool_name="discover",
            arguments={},
            response={"services": len(services), "agents": len(agent_registry)},
            status="ok",
            duration_ms=duration_ms,
            agent_id=_get_caller_name(ctx)
        )
        
        return result
    finally:
        await db.close()


@mcp.tool()
async def authenticate(token: str, ctx: Context) -> str:
    """Authenticate this session with a Motherbrain user token.
    
    Call this once per session if your MCP client config does not include
    an X-User-Token header. After authenticating, call_tool will enforce
    your user's service permissions.
    
    Args:
        token: Your Motherbrain user token (issued by an admin)
    
    Returns:
        JSON with your user info and permitted services.
    """
    from app.services.user_service import get_user_by_token, get_user_groups
    
    db = await _get_db()
    try:
        user = await get_user_by_token(db, token)
        if not user:
            return json.dumps({"error": "Invalid or expired token"})
        
        # Store token in Redis keyed by caller name for this session
        caller = _get_caller_name(ctx) or "unknown"
        await redis_queue.set_key(f"mcp_auth:{caller}", token, ttl=3600)
        
        groups = await get_user_groups(db, user.user_id)
        permitted = []
        for g in groups:
            permitted.extend(g.allowed_service_ids or [])
        
        return json.dumps({
            "authenticated": True,
            "user_id": user.user_id,
            "name": user.name,
            "role": user.role,
            "permitted_services": list(set(permitted)) if user.role != "admin" else "all"
        }, indent=2)
    finally:
        await db.close()


@mcp.tool()
async def get_system_state(ctx: Context) -> str:
    """Get full system state for situational awareness.
    
    Returns information about all registered MCP services, online agents,
    pending jobs, and recent activity. Use this first to understand
    what's available before calling other tools.
    
    Returns:
        JSON string with system state including:
        - mcp_services: count, online status, capabilities
        - agents: count, online status
        - jobs: pending and running counts
        - recent_activity: recent actions
    """
    start_time = time.time()
    db = await _get_db()
    
    try:
        state = await _get_system_state(db)
        result = json.dumps(state, indent=2)
        
        # Log this system call
        duration_ms = int((time.time() - start_time) * 1000)
        await append_event(
            topic="system",
            service_id="motherbrain",
            tool_name="get_system_state",
            arguments={},
            response={"services": state.get("mcp_services", {}).get("count", 0)},
            status="ok",
            duration_ms=duration_ms,
            agent_id=_get_caller_name(ctx)
        )
        
        return result
    finally:
        await db.close()


@mcp.tool()
async def list_tools(service_id: str, ctx: Context) -> str:
    """List available tools on a registered MCP service.
    
    Args:
        service_id: The service ID (from get_system_state)
    
    Returns:
        JSON array of tool names available on that service.
        Returns error if service not found.
    
    Example:
        list_tools("agentchattr-mcp") 
        → ["chat_send", "chat_read", "chat_join", "chat_who", ...]
    """
    start_time = time.time()
    db = await _get_db()
    
    try:
        service = await mcp_service_service.get_service(db, service_id)
        duration_ms = int((time.time() - start_time) * 1000)
        
        if not service:
            error_result = {"error": f"Service '{service_id}' not found"}
            await append_event(
                topic="system",
                service_id="motherbrain",
                tool_name="list_tools",
                arguments={"service_id": service_id},
                response=error_result,
                status="error",
                duration_ms=duration_ms,
                agent_id=_get_caller_name(ctx)
            )
            return json.dumps(error_result)
        
        tools = service.capabilities or []
        result = json.dumps({
            "service_id": service_id,
            "name": service.name,
            "status": service.status,
            "tools": tools
        }, indent=2)
        
        # Log this system call
        await append_event(
            topic="system",
            service_id="motherbrain",
            tool_name="list_tools",
            arguments={"service_id": service_id},
            response={"tools_count": len(tools)},
            status="ok",
            duration_ms=duration_ms,
            agent_id=_get_caller_name(ctx)
        )
        
        return result
    finally:
        await db.close()


@mcp.tool()
async def register_service(
    service_id: str,
    name: str,
    endpoint: str,
    ctx: Context,
    capabilities: list[str] = [],
    protocol: str = "mcp",
) -> str:
    """Register a new MCP service with Motherbrain, or update an existing one.

    Once registered, the service is health-probed immediately and every 30s
    thereafter. Use call_tool(service_id, ...) to invoke its tools.

    Args:
        service_id: Unique identifier (e.g., "my-search-service")
        name: Human-readable name (e.g., "My Search Service")
        endpoint: HTTP URL where the service is running (e.g., "http://localhost:8010")
        capabilities: List of tool names this service exposes. If omitted, Motherbrain
                      will attempt to auto-discover by calling tools/list on the endpoint.
        protocol: "mcp" for MCP JSON-RPC services (default), "rest" for legacy REST
    
    Returns:
        JSON with registered service details and initial health status.
    
    Example:
        register_service(
            "brave-search",
            "Brave Search",
            "http://localhost:8004",
            ["brave_web_search", "brave_local_search"]
        )
    """
    start_time = time.time()
    db = await _get_db()
    
    try:
        # Check if service already exists
        existing = await mcp_service_service.get_service(db, service_id)
        
        if existing:
            # Update existing service
            update_data = MCPServiceUpdate(
                name=name,
                endpoint=endpoint,
                capabilities=capabilities,
                protocol=protocol
            )
            service = await mcp_service_service.update_service(db, service_id, update_data)
            action = "updated"
        else:
            # Create new service
            create_data = MCPServiceCreate(
                service_id=service_id,
                name=name,
                endpoint=endpoint,
                capabilities=capabilities,
                protocol=protocol
            )
            service = await mcp_service_service.register_service(db, create_data)
            action = "registered"
        
        # Immediately probe the endpoint
        is_online = await _probe(endpoint)
        if not is_online:
            await mcp_service_service.update_service_status(db, service_id, "offline")
            service.status = "offline"
        
        # Auto-discover capabilities if none provided
        capabilities_discovered = False
        if not capabilities and is_online:
            discovered = await _discover_capabilities(endpoint)
            if discovered:
                capabilities = discovered
                capabilities_discovered = True
                # Update the DB with discovered capabilities
                await mcp_service_service.update_service(
                    db, service_id,
                    MCPServiceUpdate(capabilities=discovered)
                )
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        result = {
            "service_id": service.service_id,
            "name": service.name,
            "endpoint": service.endpoint,
            "capabilities": capabilities,
            "protocol": service.protocol,
            "status": service.status,
            "action": action,
            "capabilities_discovered": capabilities_discovered
        }
        
        # Log the action
        await append_event(
            topic="system",
            service_id="motherbrain",
            tool_name="register_service",
            arguments={"service_id": service_id, "name": name, "endpoint": endpoint},
            response=result,
            status="ok",
            duration_ms=duration_ms,
            agent_id=_get_caller_name(ctx)
        )
        
        return json.dumps(result, indent=2)
    finally:
        await db.close()


@mcp.tool()
async def remove_service(service_id: str, ctx: Context) -> str:
    """Unregister an MCP service from Motherbrain.

    Removes the service from the registry and stops health monitoring.
    Does not affect the service process itself.

    Args:
        service_id: The service ID to remove
    
    Returns:
        Confirmation JSON.
    """
    start_time = time.time()
    db = await _get_db()
    
    try:
        # Check if service exists
        existing = await mcp_service_service.get_service(db, service_id)
        
        if not existing:
            error_result = {"error": f"Service '{service_id}' not found"}
            duration_ms = int((time.time() - start_time) * 1000)
            await append_event(
                topic="system",
                service_id="motherbrain",
                tool_name="remove_service",
                arguments={"service_id": service_id},
                response=error_result,
                status="error",
                duration_ms=duration_ms,
                agent_id=_get_caller_name(ctx)
            )
            return json.dumps(error_result)
        
        # Delete the service
        await mcp_service_service.delete_service(db, service_id)
        
        duration_ms = int((time.time() - start_time) * 1000)
        result = {
            "service_id": service_id,
            "action": "removed"
        }
        
        # Log the action
        await append_event(
            topic="system",
            service_id="motherbrain",
            tool_name="remove_service",
            arguments={"service_id": service_id},
            response=result,
            status="ok",
            duration_ms=duration_ms,
            agent_id=_get_caller_name(ctx)
        )
        
        return json.dumps(result, indent=2)
    finally:
        await db.close()


@mcp.tool()
async def create_job(
    type: str,
    payload: dict,
    ctx: Context,
    assigned_agent: str = "",
    priority: str = "medium",
    requirements: list[str] = [],
    context_job_ids: list[str] = [],
    skill_key: str = "",
) -> str:
    """Dispatch a job to a registered agent.

    Creates a pending job that will be picked up by an agent on their next
    heartbeat. Use discover() to see which agents are online first.

    Args:
        type: Job type describing the task (e.g., "summarize", "code_review", "search")
        payload: Arbitrary dict with task data (e.g., {"text": "...", "url": "..."})
        assigned_agent: Agent name to assign directly (e.g., "kimi"). If empty,
                        any agent matching requirements can claim it.
        priority: "low", "medium" (default), or "high"
        requirements: List of agent capabilities required (e.g., ["python", "search"])
        context_job_ids: List of prior job IDs to attach as context. Their results/payloads
                         will be inlined when the agent picks up the job.
        skill_key: Key from the context/skills store to attach (e.g., "skills.code_review").
                   The skill's value will be inlined when the agent picks up the job.

    Returns:
        JSON with job_id, status, assigned_agent, and a tip to poll get_job_status.

    Example:
        create_job(
            "summarize",
            {"url": "https://example.com/article"},
            assigned_agent="kimi",
            priority="high",
            context_job_ids=["uuid-of-previous-job"],
            skill_key="skills.summarize"
        )
    """
    start_time = time.time()
    db = await _get_db()
    
    try:
        # Admin check: resolve token and verify role=admin
        token = await _resolve_user_token(ctx)
        if token:
            from app.services.user_service import get_user_by_token
            user = await get_user_by_token(db, token)
            if not user or not user.is_active or user.role != "admin":
                return json.dumps({"error": "Permission denied: Admin access required to create jobs"})
        # If no token: allowed (MCP clients without auth can create jobs for backward compat)
        
        # Resolve assigned_agent name → agent_id UUID
        resolved_agent_id = None
        if assigned_agent:
            from app.services.agent_service import get_agent_by_name
            resolved = await get_agent_by_name(db, assigned_agent)
            resolved_agent_id = resolved.agent_id if resolved else assigned_agent
        
        # Build JobCreate schema
        job_data = JobCreate(
            type=type,
            payload=payload,
            priority=priority,
            requirements=requirements,
            assigned_agent=resolved_agent_id,
            created_by=_get_caller_name(ctx) or "mcp-client",
            target_type="agent",
            context_job_ids=context_job_ids or [],
            skill_key=skill_key if skill_key else None
        )
        
        # Create the job
        job = await _create_job(db, job_data)
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        result = {
            "job_id": job.job_id,
            "type": job.type,
            "status": job.status,
            "priority": job.priority,
            "assigned_agent": job.assigned_agent,
            "assigned_agent_name": assigned_agent or None,
            "created_by": job.created_by,
            "context_job_ids": job.context_job_ids,
            "skill_key": job.skill_key,
            "tip": f"Call get_job_status('{job.job_id}') to check progress"
        }
        
        # Log the action
        await append_event(
            topic="job",
            service_id="motherbrain",
            tool_name="create_job",
            arguments={"type": type, "assigned_agent": assigned_agent, "priority": priority, "context_job_ids": context_job_ids, "skill_key": skill_key},
            response={"job_id": job.job_id, "status": job.status},
            status="ok",
            duration_ms=duration_ms,
            agent_id=_get_caller_name(ctx)
        )
        
        return json.dumps(result, indent=2)
    finally:
        await db.close()


@mcp.tool()
async def get_job_status(job_id: str, ctx: Context) -> str:
    """Check the status of a dispatched job.

    Args:
        job_id: The job UUID returned by create_job

    Returns:
        JSON with current status, assigned agent, result, and error if any.
        Status values: "pending", "assigned", "running", "completed", "failed"
    """
    start_time = time.time()
    db = await _get_db()
    
    try:
        # Get the job
        job = await get_job(db, job_id)
        
        if not job:
            error_result = {"error": f"Job '{job_id}' not found"}
            duration_ms = int((time.time() - start_time) * 1000)
            await append_event(
                topic="job",
                service_id="motherbrain",
                tool_name="get_job_status",
                arguments={"job_id": job_id},
                response=error_result,
                status="error",
                duration_ms=duration_ms,
                agent_id=_get_caller_name(ctx)
            )
            return json.dumps(error_result)
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        result = {
            "job_id": job.job_id,
            "type": job.type,
            "status": job.status,
            "assigned_agent": job.assigned_agent,
            "priority": job.priority,
            "result": job.result,
            "error": job.error,
            "created_by": job.created_by
        }
        
        # Log the action
        await append_event(
            topic="job",
            service_id="motherbrain",
            tool_name="get_job_status",
            arguments={"job_id": job_id},
            response={"status": job.status},
            status="ok",
            duration_ms=duration_ms,
            agent_id=_get_caller_name(ctx)
        )
        
        return json.dumps(result, indent=2)
    finally:
        await db.close()


async def _resolve_user_token(ctx: Context) -> str | None:
    """Resolve user token from header (via middleware) or authenticate tool (Redis).
    
    Method 1: Header token set by MCPAuthMiddleware ContextVar
    Method 2: Token stored via authenticate tool in Redis (keyed by caller name)
    
    Returns:
        The user token string, or None if not authenticated.
    """
    # Method 1: header (set by middleware ContextVar)
    token = get_current_user_token()
    if token:
        return token
    
    # Method 2: authenticate tool (stored in Redis)
    caller = _get_caller_name(ctx)
    if caller:
        token = await redis_queue.get_key(f"mcp_auth:{caller}")
        if token:
            return token
    
    return None


@mcp.tool()
async def call_tool(service_id: str, tool_name: str, arguments: dict, ctx: Context) -> str:
    """Call a tool on a registered MCP service.
    
    This is the main proxy tool — it forwards your call to the target
    MCP service, logs the result, and returns the response.
    
    The call is logged to the event log. Use get_event_log() after
    calling to see the full result and decide your next action.
    
    Args:
        service_id: Which MCP service to call (e.g., "agentchattr-mcp")
        tool_name: Which tool to invoke (e.g., "chat_send")
        arguments: Dictionary of arguments (e.g., {"channel": "general", "message": "hi"})
    
    Returns:
        The tool result as a string (usually JSON)
    
    Example:
        call_tool(
            "agentchattr-mcp",
            "chat_send",
            {"channel": "general", "message": "Hello from Motherbrain"}
        )
        → "Sent (id=123)"
    """
    db = await _get_db()
    start_time = time.time()
    topic = _infer_topic(service_id, tool_name)
    
    try:
        # Get the target service
        service = await mcp_service_service.get_service(db, service_id)
        if not service:
            error_result = {"error": f"Service '{service_id}' not found"}
            # Log the error
            duration_ms = int((time.time() - start_time) * 1000)
            await append_event(
                topic=topic,
                service_id=service_id,
                tool_name=tool_name,
                arguments=arguments,
                response=error_result,
                status="error",
                duration_ms=duration_ms,
                agent_id=_get_caller_name(ctx)
            )
            return json.dumps(error_result)
        
        if service.status != "online":
            error_result = {"error": f"Service '{service_id}' is offline"}
            # Log the error
            duration_ms = int((time.time() - start_time) * 1000)
            await append_event(
                topic=topic,
                service_id=service_id,
                tool_name=tool_name,
                arguments=arguments,
                response=error_result,
                status="error",
                duration_ms=duration_ms,
                agent_id=_get_caller_name(ctx)
            )
            return json.dumps(error_result)
        
        # Permission check
        token = await _resolve_user_token(ctx)
        if token:
            from app.services.permission_service import check_permission
            async with AsyncSessionLocal() as perm_db:
                allowed, reason = await check_permission(perm_db, token, service_id)
            if not allowed:
                error_result = {"error": f"Permission denied: {reason}"}
                await append_event(
                    topic=topic,
                    service_id=service_id,
                    tool_name=tool_name,
                    arguments=arguments,
                    response=error_result,
                    status="error",
                    duration_ms=int((time.time() - start_time) * 1000),
                    agent_id=_get_caller_name(ctx)
                )
                return json.dumps(error_result)
        # If no token: allow (unauthenticated sessions have full access for now)
        
        # Create a proxy job object (SimpleNamespace, not ORM)
        job_proxy = SimpleNamespace(
            type=tool_name,
            payload=arguments or {},
        )
        
        # Call the MCP service synchronously
        try:
            result = await mcp_proxy.call_mcp_service(service, job_proxy)
            # Log the success
            duration_ms = int((time.time() - start_time) * 1000)
            await append_event(
                topic=topic,
                service_id=service_id,
                tool_name=tool_name,
                arguments=arguments,
                response=result,
                status="ok",
                duration_ms=duration_ms,
                agent_id=_get_caller_name(ctx)
            )
            
            return json.dumps({
                "status": "success",
                "service_id": service_id,
                "tool": tool_name,
                "result": result
            }, indent=2)
        except Exception as e:
            error_result = {
                "status": "error",
                "service_id": service_id,
                "tool": tool_name,
                "error": str(e)
            }
            # Log the error
            duration_ms = int((time.time() - start_time) * 1000)
            await append_event(
                topic=topic,
                service_id=service_id,
                tool_name=tool_name,
                arguments=arguments,
                response=error_result,
                status="error",
                duration_ms=duration_ms,
                agent_id=_get_caller_name(ctx)
            )
            
            return json.dumps(error_result)
    finally:
        await db.close()


@mcp.tool()
async def get_event_log(
    limit: int = 20,
    since_id: int = 0,
    topic: str = "",
    service_id: str = ""
) -> str:
    """Read the unified activity log. Filter by topic or service_id to find events relevant to your task.
    
    Every tool call, heartbeat, and system event is logged here. Use filters
    to narrow down to events relevant to your current task.
    
    Args:
        limit: Maximum number of events to return (default 20)
        since_id: Only return events with id > since_id (use for polling)
        topic: Filter by topic — "chat" (agentchattr), "proxy" (other services),
               "heartbeat" (agent check-ins), "system" (motherbrain tools)
        service_id: Filter by service — e.g. "agentchattr-mcp", "motherbrain"
    
    Returns:
        JSON array of events, newest first. Each event contains:
        - id: Event ID (use for since_id polling)
        - timestamp: When the call was made
        - topic: Event category ("chat", "proxy", "heartbeat", "system")
        - service_id: Which service was called
        - tool_name: Which tool was invoked
        - arguments: Arguments passed
        - response: The raw response
        - status: "ok" or "error"
        - duration_ms: How long the call took
    
    Examples:
        get_event_log(limit=5) → last 5 events
        get_event_log(topic="chat") → only chat events
        get_event_log(service_id="agentchattr-mcp") → only agentchatter calls
        get_event_log(topic="chat", since_id=42) → chat events newer than #42
    """
    events = await get_events(limit=limit, since_id=since_id, topic=topic, service_id=service_id)
    return json.dumps({
        "count": len(events),
        "filters": {"topic": topic or None, "service_id": service_id or None},
        "events": events
    }, indent=2)


@mcp.tool()
async def get_context(key: str, ctx: Context) -> str:
    """Fetch a value from the shared context/skill store.

    Use the skills.* prefix to retrieve agent skills:
      get_context("skills.summarize") → returns the summarizer prompt
      get_context("skills.code_review") → returns the code review prompt

    Skills may be restricted to specific user groups. If you don't have
    permission, you'll receive a "not found" error (to avoid leaking
    existence of restricted skills).

    Args:
        key: The context key (e.g., "skills.summarize")

    Returns:
        The stored value as JSON, or an error if not found or not permitted.
    """
    from app.services.project_context_service import get_context as _get_context

    db = await _get_db()
    try:
        start = time.time()
        
        # Resolve user token for RBAC check
        token = await _resolve_user_token(ctx)
        ctx_entry = await _get_context(db, key, token=token)
        duration_ms = int((time.time() - start) * 1000)

        if not ctx_entry:
            # Return generic "not found" to avoid leaking existence of restricted skills
            result = {"error": f"Key '{key}' not found"}
            await append_event(
                topic="system",
                service_id="motherbrain",
                tool_name="get_context",
                arguments={"key": key},
                response=result,
                status="error",
                duration_ms=duration_ms,
                agent_id=_get_caller_name(ctx)
            )
            return json.dumps(result)

        result = {
            "key": ctx_entry.context_key,
            "value": ctx_entry.value,
            "description": ctx_entry.description,
            "updated_by": ctx_entry.updated_by,
            "last_updated": str(ctx_entry.last_updated),
            "category": ctx_entry.category,
            "service_id": ctx_entry.service_id
        }
        await append_event(
            topic="system",
            service_id="motherbrain",
            tool_name="get_context",
            arguments={"key": key},
            response={"found": True},
            status="ok",
            duration_ms=duration_ms,
            agent_id=_get_caller_name(ctx)
        )
        return json.dumps(result, indent=2)
    finally:
        await db.close()


@mcp.tool()
async def set_context(
    key: str,
    value_json: str,
    description: str = "",
    service_id: str = "",
    category: str = "",
    mcp_ctx: Context = None
) -> str:
    """Store a value in the shared context/skill store.

    For skills, use the skills.* prefix and put the prompt in value_json:
      set_context(
        "skills.summarize",
        '{"prompt": "Given the following text, return a concise summary..."}',
        "Summarization skill",
        service_id="my-mcp-service",
        category="nlp"
      )

    Restricted skills:
    - Set service_id to limit access to users with permission on that service
    - Only admins or users with permission on the service can create restricted skills
    - Leave service_id blank for public skills (any authenticated user)

    Args:
        key: The context key (e.g., "skills.summarize")
        value_json: JSON-encoded value to store
        description: Optional description of the entry
        service_id: Optional MCP service ID to restrict access (blank = public)
        category: Optional category tag for UI organization (e.g., "devops", "onboarding")

    Returns:
        The stored entry on success, or permission error if not allowed.
    """
    from app.services.project_context_service import create_or_update_context, check_write_permission
    from app.schemas.project_context import ProjectContextCreate

    db = await _get_db()
    try:
        start = time.time()
        try:
            value = json.loads(value_json)
        except json.JSONDecodeError as e:
            return json.dumps({"error": f"Invalid JSON: {e}"})

        # Check write permission for restricted skills
        target_service_id = service_id if service_id else None
        token = await _resolve_user_token(mcp_ctx)

        if target_service_id:
            if not token:
                return json.dumps({"error": "Authentication required to write restricted skills"})
            allowed, reason = await check_write_permission(db, token, target_service_id)
            if not allowed:
                return json.dumps({"error": f"Permission denied: {reason}"})

        ctx = await create_or_update_context(
            db, key, ProjectContextCreate(
                value=value,
                updated_by="motherbrain-mcp",
                description=description or None,
                service_id=target_service_id,
                category=category if category else None
            )
        )
        duration_ms = int((time.time() - start) * 1000)
        result = {
            "key": ctx.context_key,
            "value": ctx.value,
            "description": ctx.description,
            "service_id": ctx.service_id,
            "category": ctx.category
        }
        await append_event(
            topic="system",
            service_id="motherbrain",
            tool_name="set_context",
            arguments={"key": key, "service_id": target_service_id, "category": category},
            response={"stored": True},
            status="ok",
            duration_ms=duration_ms,
            agent_id=_get_caller_name(mcp_ctx) if mcp_ctx else None
        )
        return json.dumps(result, indent=2)
    finally:
        await db.close()


# ── Chat Tools ───────────────────────────────────────────────────────────────
# These tools provide agents with chat capabilities integrated into Motherbrain.
# They replace the external agentchattr-mcp service.

@mcp.tool()
async def chat_join(sender: str, channel: str, ctx: Context) -> str:
    """Join a chat channel and announce your presence.
    
    Call this when you first connect to a channel to let others know you're here.
    This posts a system join message to the channel.
    
    Args:
        sender: Your agent name (e.g., "claude", "kimi")
        channel: The channel name to join (e.g., "general", "motherbrain")
    
    Returns:
        Confirmation that you joined the channel.
    """
    db = await _get_db()
    try:
        from app.api.routes.chat import _save_and_broadcast_message
        
        # Post join message
        result = await _save_and_broadcast_message(
            db, channel, "system", f"{sender} joined the channel", "join"
        )
        
        # Update presence in Redis
        await redis_queue.set_key(f"chat_presence:{channel}:{sender}", "1", ttl=30)
        
        return json.dumps({"status": "joined", "channel": channel, "sender": sender})
    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        await db.close()


@mcp.tool()
async def chat_send(
    sender: str,
    message: str,
    channel: str,
    ctx: Context,
    reply_to: int = 0,
    hop: int = 0,
) -> str:
    """Send a message to a chat channel.
    
    This is how you communicate with humans and other agents in real-time.
    Messages are persisted and broadcast to all connected clients.
    
    Args:
        sender: Your agent name
        message: The message text to send
        channel: The channel name (e.g., "general", "motherbrain")
        reply_to: Optional message ID this is a reply to
        hop: Hop count for loop guard (incremented by agents on each relay)
    
    Returns:
        Confirmation with the message ID.
    
    Example:
        chat_send("claude", "I'll analyze that file now", "general")
    """
    # Loop guard: check hop limit
    CHAT_HOP_LIMIT = int(os.getenv("CHAT_HOP_LIMIT", "5"))
    if hop >= CHAT_HOP_LIMIT:
        return json.dumps({
            "error": f"Loop guard: hop limit {CHAT_HOP_LIMIT} reached. Conversation stopped."
        })
    
    db = await _get_db()
    try:
        from app.api.routes.chat import _save_and_broadcast_message
        
        reply_id = reply_to if reply_to > 0 else None
        result = await _save_and_broadcast_message(
            db, channel, sender, message, "chat", reply_id, hop
        )
        
        # Update presence
        await redis_queue.set_key(f"chat_presence:{channel}:{sender}", "1", ttl=30)
        
        return json.dumps({
            "status": "sent",
            "message_id": result["id"],
            "channel": channel
        })
    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        await db.close()


@mcp.tool()
async def chat_read(
    sender: str,
    channel: str,
    ctx: Context,
    limit: int = 50,
    since_id: int = 0,
) -> str:
    """Read messages from a chat channel.
    
    Use this to check for new messages addressed to you or to catch up
    on conversation history. The since_id parameter lets you poll efficiently
    — only get messages newer than your last read.
    
    Args:
        sender: Your agent name (used for cursor tracking)
        channel: The channel to read from
        limit: Maximum messages to return (default 50, max 100)
        since_id: Only return messages with ID > this (for polling)
    
    Returns:
        JSON with messages array and your new cursor position.
    
    Example:
        chat_read("claude", "general", since_id=42) → messages newer than #42
    """
    db = await _get_db()
    try:
        from sqlalchemy import select, desc
        from app.models.channel import Channel
        from app.models.chat_message import ChatMessage
        
        # Get channel
        result = await db.execute(select(Channel).where(Channel.name == channel))
        ch = result.scalar_one_or_none()
        if not ch:
            return json.dumps({"error": f"Channel '{channel}' not found"})
        
        # Build query
        query = select(ChatMessage).where(ChatMessage.channel_id == ch.id)
        if since_id > 0:
            query = query.where(ChatMessage.id > since_id)
        query = query.order_by(desc(ChatMessage.id)).limit(min(limit, 100))
        
        result = await db.execute(query)
        messages = result.scalars().all()
        
        # Get cursor for next read
        new_cursor = max((m.id for m in messages), default=since_id)
        
        # Update presence
        await redis_queue.set_key(f"chat_presence:{channel}:{sender}", "1", ttl=30)
        
        return json.dumps({
            "channel": channel,
            "messages": [
                {
                    "id": m.id,
                    "sender": m.sender,
                    "text": m.text,
                    "type": m.type,
                    "reply_to": m.reply_to,
                    "created_at": m.created_at.isoformat()
                }
                for m in reversed(messages)  # Oldest first
            ],
            "cursor": new_cursor,
            "count": len(messages)
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        await db.close()


@mcp.tool()
async def chat_who(channel: str, ctx: Context) -> str:
    """List agents currently active in a channel.
    
    Returns agents who have been active in the last 30 seconds.
    Use this to see who's available to collaborate.
    
    Args:
        channel: The channel to check
    
    Returns:
        JSON array of active agent names.
    """
    try:
        # Scan for presence keys
        pattern = f"chat_presence:{channel}:*"
        keys = await redis_queue.redis.keys(pattern)
        
        agents = []
        for key in keys:
            # Extract sender name from key
            parts = key.decode().split(":")
            if len(parts) >= 3:
                agents.append(parts[2])
        
        return json.dumps({
            "channel": channel,
            "agents": sorted(agents),
            "count": len(agents)
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})
