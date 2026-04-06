"""Tests for MCP routing and proxy execution.

These tests verify that jobs with target_type="mcp" are correctly
routed to MCP services and that the proxy execution works.
"""

import respx
import httpx
from httpx import Response
import pytest

from app.services import router, mcp_proxy
from app.services import mcp_service_service
from app.services import job_service
from app.schemas.job import JobCreate
from app.schemas.mcp_service import MCPServiceCreate


@respx.mock
async def test_job_routes_to_mcp_service(db_session):
    """Test that a job with target_type='mcp' routes to an online MCP service.
    
    This test verifies:
    1. Service registration and heartbeat
    2. Job creation with target_type='mcp'
    3. Router matches job to service by capabilities
    4. Result is stored on the job
    """
    # Register and bring online an MCP service
    await mcp_service_service.register_service(db_session, MCPServiceCreate(
        service_id='router-test',
        name='Router Test',
        endpoint='http://mock-mcp',
        capabilities=['echo'],
        api_key=None
    ))
    await mcp_service_service.update_heartbeat(db_session, 'router-test')
    
    # Mock the outbound call to the MCP service
    respx.post("http://mock-mcp/execute").mock(
        return_value=Response(200, json={"result": {"echo": "hello"}})
    )
    
    # Create a job targeting MCP
    job = await job_service.create_job(db_session, JobCreate(
        type="echo",
        target_type="mcp",
        requirements=["echo"],
        payload={"message": "hello"}
    ))
    
    # Route the job
    route = await router.route_job(job, db_session)
    assert route["type"] == "mcp"
    assert route["target"].service_id == "router-test"
    
    # Execute via proxy
    result = await mcp_proxy.call_mcp_service(route["target"], job)
    assert result["result"]["echo"] == "hello"


async def test_no_mcp_service_raises(db_session):
    """Test that NoMCPServiceAvailable is raised when no matching service exists."""
    from app.exceptions import NoMCPServiceAvailable
    
    job = await job_service.create_job(db_session, JobCreate(
        type="unsupported",
        target_type="mcp",
        requirements=["does_not_exist"],
        payload={}
    ))
    
    with pytest.raises(NoMCPServiceAvailable):
        await router.route_job(job, db_session)


async def test_no_online_mcp_service_raises(db_session):
    """Test that offline services are not considered for routing."""
    from app.exceptions import NoMCPServiceAvailable
    
    # Register but don't send heartbeat (stays offline)
    await mcp_service_service.register_service(db_session, MCPServiceCreate(
        service_id='offline-svc',
        name='Offline Service',
        endpoint='http://offline',
        capabilities=['test'],
        api_key=None
    ))
    
    job = await job_service.create_job(db_session, JobCreate(
        type="test",
        target_type="mcp",
        requirements=["test"],
        payload={}
    ))
    
    with pytest.raises(NoMCPServiceAvailable):
        await router.route_job(job, db_session)


@respx.mock
async def test_mcp_timeout_captured(db_session):
    """Test that MCP service timeout raises MCPServiceTimeout."""
    from app.exceptions import MCPServiceTimeout
    
    # Register and bring online
    await mcp_service_service.register_service(db_session, MCPServiceCreate(
        service_id='timeout-svc',
        name='Timeout',
        endpoint='http://timeout-mcp',
        capabilities=['slow'],
        api_key=None
    ))
    await mcp_service_service.update_heartbeat(db_session, 'timeout-svc')
    
    # Mock timeout
    respx.post("http://timeout-mcp/execute").mock(
        side_effect=httpx.TimeoutException("Request timed out")
    )
    
    job = await job_service.create_job(db_session, JobCreate(
        type="slow",
        target_type="mcp",
        requirements=["slow"],
        payload={}
    ))
    
    route = await router.route_job(job, db_session)
    
    with pytest.raises(MCPServiceTimeout):
        await mcp_proxy.call_mcp_service(route["target"], job, timeout=0.001)


@respx.mock
async def test_mcp_http_error_captured(db_session):
    """Test that MCP service HTTP errors raise MCPServiceError."""
    from app.exceptions import MCPServiceError
    
    # Register and bring online
    await mcp_service_service.register_service(db_session, MCPServiceCreate(
        service_id='error-svc',
        name='Error Service',
        endpoint='http://error-mcp',
        capabilities=['fail'],
        api_key=None
    ))
    await mcp_service_service.update_heartbeat(db_session, 'error-svc')
    
    # Mock HTTP error
    respx.post("http://error-mcp/execute").mock(
        return_value=Response(500, json={"error": "Internal Server Error"})
    )
    
    job = await job_service.create_job(db_session, JobCreate(
        type="fail",
        target_type="mcp",
        requirements=["fail"],
        payload={}
    ))
    
    route = await router.route_job(job, db_session)
    
    with pytest.raises(MCPServiceError):
        await mcp_proxy.call_mcp_service(route["target"], job)


async def test_capability_matching(db_session):
    """Test that router correctly matches jobs to services by capabilities."""
    # Register two services with different capabilities
    await mcp_service_service.register_service(db_session, MCPServiceCreate(
        service_id='code-svc',
        name='Code Service',
        endpoint='http://code',
        capabilities=['generate_code', 'python'],
        api_key=None
    ))
    await mcp_service_service.update_heartbeat(db_session, 'code-svc')
    
    await mcp_service_service.register_service(db_session, MCPServiceCreate(
        service_id='text-svc',
        name='Text Service',
        endpoint='http://text',
        capabilities=['summarize', 'translate'],
        api_key=None
    ))
    await mcp_service_service.update_heartbeat(db_session, 'text-svc')
    
    # Job requiring code generation
    code_job = await job_service.create_job(db_session, JobCreate(
        type="generate_code",
        target_type="mcp",
        requirements=["generate_code", "python"],
        payload={"prompt": "hello world"}
    ))
    
    route = await router.route_job(code_job, db_session)
    assert route["target"].service_id == "code-svc"
    
    # Job requiring text summarization
    text_job = await job_service.create_job(db_session, JobCreate(
        type="summarize",
        target_type="mcp",
        requirements=["summarize"],
        payload={"text": "long text..."}
    ))
    
    route = await router.route_job(text_job, db_session)
    assert route["target"].service_id == "text-svc"


async def test_partial_capability_match_fails(db_session):
    """Test that router requires ALL job requirements to be met."""
    from app.exceptions import NoMCPServiceAvailable
    
    # Service has only one of two required capabilities
    await mcp_service_service.register_service(db_session, MCPServiceCreate(
        service_id='partial-svc',
        name='Partial',
        endpoint='http://partial',
        capabilities=['python'],  # Missing 'javascript'
        api_key=None
    ))
    await mcp_service_service.update_heartbeat(db_session, 'partial-svc')
    
    job = await job_service.create_job(db_session, JobCreate(
        type="multi-lang",
        target_type="mcp",
        requirements=["python", "javascript"],  # Both required
        payload={}
    ))
    
    with pytest.raises(NoMCPServiceAvailable):
        await router.route_job(job, db_session)
