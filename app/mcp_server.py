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
from types import SimpleNamespace
from mcp.server.fastmcp import FastMCP

from app.db.session import AsyncSessionLocal
from app.services.system_state import get_system_state as _get_system_state
from app.services import mcp_service_service, mcp_proxy


async def _get_db():
    """Get a database session."""
    async with AsyncSessionLocal() as session:
        return session


# Create FastMCP server
mcp = FastMCP(
    "motherbrain",
    host="0.0.0.0",
    port=8300,
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
    db = await _get_db()
    try:
        state = await _get_system_state(db)
        return json.dumps(state, indent=2)
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
    db = await _get_db()
    try:
        service = await mcp_service_service.get_service(db, service_id)
        if not service:
            return json.dumps({"error": f"Service '{service_id}' not found"})
        
        tools = service.capabilities or []
        return json.dumps({
            "service_id": service_id,
            "name": service.name,
            "status": service.status,
            "tools": tools
        }, indent=2)
    finally:
        await db.close()


@mcp.tool()
async def call_tool(service_id: str, tool_name: str, arguments: dict) -> str:
    """Call a tool on a registered MCP service.
    
    This is the main proxy tool — it forwards your call to the target
    MCP service and returns the result synchronously.
    
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
    try:
        # Get the target service
        service = await mcp_service_service.get_service(db, service_id)
        if not service:
            return json.dumps({"error": f"Service '{service_id}' not found"})
        
        if service.status != "online":
            return json.dumps({"error": f"Service '{service_id}' is offline"})
        
        # Create a proxy job object (SimpleNamespace, not ORM)
        job_proxy = SimpleNamespace(
            type=tool_name,
            payload=arguments or {},
        )
        
        # Call the MCP service synchronously
        try:
            result = await mcp_proxy.call_mcp_service(service, job_proxy)
            return json.dumps({
                "status": "success",
                "service_id": service_id,
                "tool": tool_name,
                "result": result
            }, indent=2)
        except Exception as e:
            return json.dumps({
                "status": "error",
                "service_id": service_id,
                "tool": tool_name,
                "error": str(e)
            })
    finally:
        await db.close()
