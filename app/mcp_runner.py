"""MCP Server Runner — Entry point for the Motherbrain MCP server.

This runs as a separate process alongside the FastAPI HTTP server.
It provides the MCP interface (port 8300) while FastAPI handles
the HTTP API (port 8000).

Usage:
    python -m app.mcp_runner

Or via docker-compose (see Dockerfile).
"""

import asyncio
import sys

# Add parent to path for imports
sys.path.insert(0, '/app')

from app.db.session import AsyncSessionLocal
from app.mcp_server import mcp, set_db_session_factory


def main():
    """Run the Motherbrain MCP server."""
    # Set up DB session factory for the MCP server
    set_db_session_factory(AsyncSessionLocal)
    
    print("Starting Motherbrain MCP server on port 8300...")
    print("Tools available:")
    print("  - get_system_state()")
    print("  - list_tools(service_id)")
    print("  - call_tool(service_id, tool_name, arguments)")
    print("  - chat_send(channel, message, sender)")
    print("  - chat_read(channel, limit, sender)")
    
    # Run the MCP server
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
