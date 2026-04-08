"""Motherbrain MCP Server — Meta-tools for proxying to registered MCP services.

This FastMCP server exposes tools that let LLMs discover, manage, and call
any registered MCP service through Motherbrain:

Discovery & Management:
- discover() — Live orientation to the system
- get_system_state() — Full system state as JSON
- list_tools(service_id) — List tools on a specific service
- register_service(...) — Register or update an MCP service
- remove_service(service_id) — Unregister a service

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
    capabilities: list[str],
    ctx: Context,
    protocol: str = "mcp",
) -> str:
    """Register a new MCP service with Motherbrain, or update an existing one.

    Once registered, the service is health-probed immediately and every 30s
    thereafter. Use call_tool(service_id, ...) to invoke its tools.

    Args:
        service_id: Unique identifier (e.g., "my-search-service")
        name: Human-readable name (e.g., "My Search Service")
        endpoint: HTTP URL where the service is running (e.g., "http://localhost:8010")
        capabilities: List of tool names this service exposes (e.g., ["search", "index"])
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
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        result = {
            "service_id": service.service_id,
            "name": service.name,
            "endpoint": service.endpoint,
            "capabilities": service.capabilities,
            "protocol": service.protocol,
            "status": service.status,
            "action": action
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
async def get_context(key: str, mcp_ctx: Context) -> str:
    """Fetch a value from the shared context/skill store.

    Use the skills.* prefix to retrieve agent skills:
      get_context("skills.summarize") → returns the summarizer prompt
      get_context("skills.code_review") → returns the code review prompt

    Returns the stored value as JSON, or an error if the key doesn't exist.
    """
    from app.services.project_context_service import get_context as _get_context

    db = await _get_db()
    try:
        start = time.time()
        ctx = await _get_context(db, key)
        duration_ms = int((time.time() - start) * 1000)

        if not ctx:
            result = {"error": f"Key '{key}' not found"}
            await append_event(
                topic="system",
                service_id="motherbrain",
                tool_name="get_context",
                arguments={"key": key},
                response=result,
                status="error",
                duration_ms=duration_ms,
                agent_id=_get_caller_name(mcp_ctx)
            )
            return json.dumps(result)

        result = {
            "key": ctx.context_key,
            "value": ctx.value,
            "description": ctx.description,
            "updated_by": ctx.updated_by,
            "last_updated": str(ctx.last_updated)
        }
        await append_event(
            topic="system",
            service_id="motherbrain",
            tool_name="get_context",
            arguments={"key": key},
            response={"found": True},
            status="ok",
            duration_ms=duration_ms,
            agent_id=_get_caller_name(mcp_ctx)
        )
        return json.dumps(result, indent=2)
    finally:
        await db.close()


@mcp.tool()
async def set_context(key: str, value_json: str, description: str = "", mcp_ctx: Context = None) -> str:
    """Store a value in the shared context/skill store.

    For skills, use the skills.* prefix and put the prompt in value_json:
      set_context(
        "skills.summarize",
        '{"prompt": "Given the following text, return a concise summary..."}',
        "Summarization skill"
      )

    value_json must be valid JSON.
    Returns the stored entry on success.
    """
    from app.services.project_context_service import create_or_update_context
    from app.schemas.project_context import ProjectContextCreate

    db = await _get_db()
    try:
        start = time.time()
        try:
            value = json.loads(value_json)
        except json.JSONDecodeError as e:
            return json.dumps({"error": f"Invalid JSON: {e}"})

        ctx = await create_or_update_context(
            db, key, ProjectContextCreate(
                value=value,
                updated_by="motherbrain-mcp",
                description=description or None,
            )
        )
        duration_ms = int((time.time() - start) * 1000)
        result = {
            "key": ctx.context_key,
            "value": ctx.value,
            "description": ctx.description
        }
        await append_event(
            topic="system",
            service_id="motherbrain",
            tool_name="set_context",
            arguments={"key": key},
            response={"stored": True},
            status="ok",
            duration_ms=duration_ms,
            agent_id=_get_caller_name(mcp_ctx) if mcp_ctx else None
        )
        return json.dumps(result, indent=2)
    finally:
        await db.close()
