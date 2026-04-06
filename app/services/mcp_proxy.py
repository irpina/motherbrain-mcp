"""MCP Proxy Service — Calls MCP services on behalf of jobs.

This module handles HTTP communication with registered MCP services,
including authentication, timeout handling, and error capture.

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
    
    This function acts as a proxy between Motherbrain and an MCP service,
    forwarding the job payload and returning the result.
    
    Args:
        service: The MCP service to call
        job: The job to execute
        timeout: Request timeout in seconds (default: 30)
    
    Returns:
        The MCP service response as a dict
    
    Raises:
        MCPServiceTimeout: If the request times out
        MCPServiceError: If the service returns an error status
    
    Example:
        >>> service = await get_mcp_service(db, "mcp-001")
        >>> job = await get_job(db, "job-123")
        >>> result = await call_mcp_service(service, job)
        >>> print(result["code"])
    """
    # Prepare headers with API key if available
    headers = {"Content-Type": "application/json"}
    if service.api_key_hash:
        # TODO: In production, retrieve the actual API key from secrets manager
        # For MVP, we pass a placeholder - the actual key exchange needs
        # to be implemented based on your security requirements
        headers["X-API-Key"] = service.api_key_hash
    
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{service.endpoint}/execute",
                json={
                    "job_id": job.job_id,
                    "payload": job.payload
                },
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
    import uuid
    return f"mcp_{uuid.uuid4().hex}"


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
