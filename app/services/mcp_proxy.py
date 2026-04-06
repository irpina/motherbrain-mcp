"""MCP Proxy Service — Calls MCP services on behalf of jobs.

This module handles HTTP communication with registered MCP services,
including authentication, timeout handling, and error capture.

Protocol Support:
    - REST: Plain HTTP POST to {endpoint}/execute
    - MCP: JSON-RPC 2.0 to {endpoint}/mcp (Model Context Protocol)

Note:
    This is a simple proxy for MVP. Future enhancements:
    - Retry logic with exponential backoff
    - Circuit breaker pattern
    - Connection pooling
    - Streaming response support
"""

import hashlib
import time
from typing import Optional
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


async def _call_mcp_native(service: MCPService, job: Job, timeout: float) -> dict:
    """MCP JSON-RPC path: POST {endpoint}/mcp with tools/call
    
    For services speaking the Model Context Protocol (JSON-RPC 2.0).
    
    job.type = tool name (e.g., "chat_send")
    job.payload = tool arguments dict
    """
    rpc_payload = {
        "jsonrpc": "2.0",
        "id": str(uuid4()),
        "method": "tools/call",
        "params": {
            "name": job.type,
            "arguments": job.payload
        }
    }
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"
    }
    
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{service.endpoint}/mcp",
                json=rpc_payload,
                headers=headers
            )
            response.raise_for_status()
            data = response.json()
        
        # MCP JSON-RPC error response
        if "error" in data:
            err = data["error"]
            raise MCPServiceError(
                service.service_id,
                f"MCP error {err.get('code', '?')}: {err.get('message', 'unknown')}"
            )
        
        # Unwrap MCP result — content is a list of blocks
        result = data.get("result", {})
        content = result.get("content", [])
        # Flatten text blocks into a single result dict
        text_parts = [block["text"] for block in content if block.get("type") == "text"]
        return {
            "mcp_result": result,
            "text": "\n".join(text_parts) if text_parts else None
        }
        
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
