"""MCP Proxy Service — Calls MCP services on behalf of jobs.

This module handles HTTP communication with registered MCP services,
including authentication, timeout handling, and error capture.

Protocol Support:
    - REST: Plain HTTP POST to {endpoint}/execute
    - MCP: JSON-RPC 2.0 with session handshake to {endpoint}/mcp

Note:
    This is a simple proxy for MVP. Future enhancements:
    - Retry logic with exponential backoff
    - Circuit breaker pattern
    - Connection pooling
    - Streaming response support
"""

import hashlib
import json
import time
from typing import Optional
from urllib.parse import urlparse
from uuid import uuid4

import httpx

from app.models.job import Job
from app.models.mcp_service import MCPService
from app.exceptions import MCPServiceTimeout, MCPServiceError


async def call_mcp_service(
    service: MCPService, 
    job: Job,
    timeout: float = 30.0
) -> dict:
    """Execute a job by calling an MCP service.
    
    Routes to REST or MCP-native execution based on service.protocol.
    
    Args:
        service: The MCP service to call
        job: The job to execute
        timeout: Request timeout in seconds (default: 30)
    
    Returns:
        The MCP service response as a dict
    
    Raises:
        MCPServiceTimeout: If the request times out
        MCPServiceError: If the service returns an error status
    """
    if service.protocol == "mcp":
        return await _call_mcp_native(service, job, timeout)
    return await _call_rest_execute(service, job, timeout)


async def _call_rest_execute(service: MCPService, job: Job, timeout: float) -> dict:
    """Original REST path: POST {endpoint}/execute
    
    For services using the simple REST execution protocol.
    """
    headers = {"Content-Type": "application/json"}
    if service.api_key_hash:
        headers["X-API-Key"] = service.api_key_hash
    
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{service.endpoint}/execute",
                json={"job_id": job.job_id, "payload": job.payload},
                headers=headers
            )
            response.raise_for_status()
            return response.json()
            
    except httpx.TimeoutException as e:
        raise MCPServiceTimeout(service.service_id) from e
    except httpx.HTTPStatusError as e:
        raise MCPServiceError(
            service.service_id,
            f"HTTP {e.response.status_code}: {e.response.text}"
        ) from e
    except httpx.RequestError as e:
        raise MCPServiceError(
            service.service_id,
            f"Request failed: {str(e)}"
        ) from e


def _parse_mcp_response_body(response: httpx.Response) -> dict:
    """Parse an MCP response that may be plain JSON or Server-Sent Events.

    Some MCP servers (e.g. FastMCP with streamable-http transport) return
    Content-Type: text/event-stream even for single-shot tool calls. The body
    looks like:

        event: message
        data: {"jsonrpc": "2.0", "id": "...", "result": {...}}

    This helper extracts the JSON payload regardless of encoding.
    """
    content_type = response.headers.get("content-type", "")
    if "text/event-stream" in content_type:
        for line in response.text.splitlines():
            if line.startswith("data:"):
                payload = line[len("data:"):].strip()
                if payload:
                    return json.loads(payload)
        raise ValueError("SSE response contained no data line")
    return response.json()


async def _call_mcp_native(service: MCPService, job: Job, timeout: float) -> dict:
    """MCP JSON-RPC path with full session handshake.

    Flow: initialize → notifications/initialized → tools/call
    Session ID is returned in the 'mcp-session-id' response header.
    """
    parsed = urlparse(service.endpoint)
    port_str = f":{parsed.port}" if parsed.port else ""
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        # Override Host to localhost so the MCP server's DNS-rebinding protection
        # accepts requests originating from Docker (host.docker.internal).
        "Host": f"localhost{port_str}",
    }
    mcp_url = f"{service.endpoint}/mcp"

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:

            # Step 1: Initialize session
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
            if not session_id:
                raise MCPServiceError(service.service_id, "MCP server did not return a session ID")

            session_headers = {**headers, "mcp-session-id": session_id}

            # Step 2: Send initialized notification (no response expected)
            await client.post(mcp_url, headers=session_headers, json={
                "jsonrpc": "2.0",
                "method": "notifications/initialized"
            })

            # Step 3: Call the tool
            call_resp = await client.post(mcp_url, headers=session_headers, json={
                "jsonrpc": "2.0",
                "id": str(uuid4()),
                "method": "tools/call",
                "params": {
                    "name": job.type,
                    "arguments": job.payload
                }
            })
            call_resp.raise_for_status()
            data = _parse_mcp_response_body(call_resp)

        if "error" in data:
            err = data["error"]
            raise MCPServiceError(
                service.service_id,
                f"MCP error {err.get('code', '?')}: {err.get('message', 'unknown')}"
            )

        result = data.get("result", {})
        content = result.get("content", [])
        text_parts = [block["text"] for block in content if block.get("type") == "text"]
        return {
            "mcp_result": result,
            "text": "\n".join(text_parts) if text_parts else None
        }

    except httpx.TimeoutException as e:
        raise MCPServiceTimeout(service.service_id) from e
    except httpx.HTTPStatusError as e:
        raise MCPServiceError(service.service_id, f"HTTP {e.response.status_code}: {e.response.text}") from e
    except httpx.RequestError as e:
        raise MCPServiceError(service.service_id, f"Request failed: {str(e)}") from e


def hash_api_key(api_key: str) -> str:
    """Hash an API key for storage.
    
    Uses SHA-256 to create a one-way hash of the API key.
    The original key is returned to the client once at registration
    and should be stored securely by the client.
    
    Args:
        api_key: The raw API key
    
    Returns:
        SHA-256 hash of the key
    """
    return hashlib.sha256(api_key.encode()).hexdigest()


def generate_api_key() -> str:
    """Generate a new random API key.
    
    Returns:
        A new UUID-based API key
    """
    return f"mcp_{uuid4().hex}"


# FUTURE: Implement retry logic
async def call_mcp_service_with_retry(
    service: MCPService,
    job: Job,
    max_retries: int = 3,
    base_delay: float = 1.0
) -> dict:
    """Call MCP service with exponential backoff retry.
    
    Future enhancement: Implement retry logic for transient failures.
    
    Args:
        service: The MCP service to call
        job: The job to execute
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay between retries (doubles each time)
    
    Returns:
        The service response
    
    Raises:
        MCPServiceError: If all retries fail
    """
    raise NotImplementedError("Retry logic not yet implemented")


# FUTURE: Implement circuit breaker
class CircuitBreaker:
    """Circuit breaker pattern for MCP service calls.
    
    Future enhancement: Prevent cascade failures by stopping calls
    to services that are consistently failing.
    
    States:
        CLOSED: Normal operation, calls pass through
        OPEN: Service failing, calls fail fast
        HALF_OPEN: Testing if service recovered
    """
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.last_failure_time: Optional[float] = None
        self.state = "CLOSED"
    
    async def call(self, func, *args, **kwargs):
        """Execute a call with circuit breaker protection."""
        raise NotImplementedError("Circuit breaker not yet implemented")
