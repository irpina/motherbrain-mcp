"""Motherbrain MCP Server — Meta-tools for proxying to registered MCP services.

This FastMCP server exposes 3 tools that let LLMs discover and call
any registered MCP service through Motherbrain:

1. get_system_state() — Discover what's available
2. list_tools(service_id) — List tools on a specific service  
3. call_tool(service_id, tool_name, arguments) — Route calls to target MCP

The LLM connects to Motherbrain (port 8000/mcp) and can access ALL
registered MCP services through a single endpoint.
"""

import json
import time
from datetime import datetime, timezone, timedelta
from types import SimpleNamespace
from mcp.server.fastmcp import FastMCP

from app.db.session import AsyncSessionLocal
from app.services.system_state import get_system_state as _get_system_state
from app.services import mcp_service_service, mcp_proxy
from app.services.event_log import append_event, get_events
from app.services.agent_registry import agent_registry


async def _get_db():
    """Get a database session."""
    async with AsyncSessionLocal() as session:
        return session


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
        "Motherbrain MCP Server — Gateway to registered MCP services.\n\n"
        "Use get_system_state() to discover what's available.\n"
        "Use list_tools(service_id) to see tools on a specific service.\n"
        "Use call_tool(service_id, tool_name, arguments) to invoke any tool.\n\n"
        "Example flow:\n"
        "1. get_system_state() → see registered MCP services\n"
        "2. list_tools('agentchattr-mcp') → ['chat_send', 'chat_read', ...]\n"
        "3. call_tool('agentchattr-mcp', 'chat_send', {\"channel\": \"general\", \"message\": \"hello\"})"
    ),
)


@mcp.tool()
async def discover() -> str:
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
            if age < 60:
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
"""
        # Log this system call
        duration_ms = int((time.time() - start_time) * 1000)
        append_event(
            topic="system",
            service_id="motherbrain",
            tool_name="discover",
            arguments={},
            response={"services": len(services), "agents": len(agent_registry)},
            status="ok",
            duration_ms=duration_ms
        )
        
        return result
    finally:
        await db.close()


@mcp.tool()
async def get_system_state() -> str:
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
        append_event(
            topic="system",
            service_id="motherbrain",
            tool_name="get_system_state",
            arguments={},
            response={"services": state.get("mcp_services", {}).get("count", 0)},
            status="ok",
            duration_ms=duration_ms
        )
        
        return result
    finally:
        await db.close()


@mcp.tool()
async def list_tools(service_id: str) -> str:
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
            append_event(
                topic="system",
                service_id="motherbrain",
                tool_name="list_tools",
                arguments={"service_id": service_id},
                response=error_result,
                status="error",
                duration_ms=duration_ms
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
        append_event(
            topic="system",
            service_id="motherbrain",
            tool_name="list_tools",
            arguments={"service_id": service_id},
            response={"tools_count": len(tools)},
            status="ok",
            duration_ms=duration_ms
        )
        
        return result
    finally:
        await db.close()


@mcp.tool()
async def call_tool(service_id: str, tool_name: str, arguments: dict) -> str:
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
            append_event(
                topic=topic,
                service_id=service_id,
                tool_name=tool_name,
                arguments=arguments,
                response=error_result,
                status="error",
                duration_ms=duration_ms
            )
            return json.dumps(error_result)
        
        if service.status != "online":
            error_result = {"error": f"Service '{service_id}' is offline"}
            # Log the error
            duration_ms = int((time.time() - start_time) * 1000)
            append_event(
                topic=topic,
                service_id=service_id,
                tool_name=tool_name,
                arguments=arguments,
                response=error_result,
                status="error",
                duration_ms=duration_ms
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
            append_event(
                topic=topic,
                service_id=service_id,
                tool_name=tool_name,
                arguments=arguments,
                response=result,
                status="ok",
                duration_ms=duration_ms
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
            append_event(
                topic=topic,
                service_id=service_id,
                tool_name=tool_name,
                arguments=arguments,
                response=error_result,
                status="error",
                duration_ms=duration_ms
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
    events = get_events(limit=limit, since_id=since_id, topic=topic, service_id=service_id)
    return json.dumps({
        "count": len(events),
        "filters": {"topic": topic or None, "service_id": service_id or None},
        "events": events
    }, indent=2)
