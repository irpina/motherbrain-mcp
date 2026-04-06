"""Router Service — Routes jobs to agents or MCP services.

This module contains the routing logic that determines whether a job
should be executed by an agent or an MCP service, and selects the
appropriate target based on capabilities and availability.

Extension Points:
    - Add load balancing logic to select_best_agent()
    - Add retry logic for failed routing attempts
    - Add topic-based routing when pub/sub is implemented
"""

from typing import Optional, Union
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job
from app.models.agent import Agent
from app.models.mcp_service import MCPService
from app.exceptions import NoAgentAvailable, NoMCPServiceAvailable
from app.services import agent_service, mcp_service_service


async def route_job(job: Job, db: AsyncSession) -> dict:
    """Route a job to the appropriate target (agent or MCP service).
    
    This is the main entry point for job routing. It examines the job's
    target_type and delegates to the appropriate matcher.
    
    Args:
        job: The job to route
        db: Database session
    
    Returns:
        Dict with "type" ("agent" or "mcp") and "target" (Agent or MCPService)
    
    Raises:
        NoAgentAvailable: If target_type is "agent" and no suitable agent exists
        NoMCPServiceAvailable: If target_type is "mcp" and no suitable service exists
        ValueError: If target_type is unknown
    """
    if job.target_type == "agent":
        agents = await agent_service.list_agents(db)
        agent = match_job_to_agent(job, agents)
        if not agent:
            raise NoAgentAvailable(job.job_id)
        return {"type": "agent", "target": agent}
    
    if job.target_type == "mcp":
        # Direct targeting: caller specified exact service
        if job.target_service_id:
            service = await mcp_service_service.get_service(db, job.target_service_id)
            if not service:
                raise NoMCPServiceAvailable(job.job_id)
            return {"type": "mcp", "target": service}
        
        # Capability-based matching (existing logic)
        services = await mcp_service_service.list_services(db)
        service = match_job_to_mcp(job, services)
        if not service:
            raise NoMCPServiceAvailable(job.job_id)
        return {"type": "mcp", "target": service}
    
    raise ValueError(f"Unknown target_type: {job.target_type}")


def match_job_to_agent(job: Job, agents: list[Agent]) -> Optional[Agent]:
    """Match a job to an available agent based on capabilities.
    
    This function implements the core matching algorithm that finds
    an agent that is online and has all required capabilities.
    
    Args:
        job: The job to match
        agents: List of all registered agents
    
    Returns:
        The best matching agent, or None if no match found
    
    Note:
        Currently implements simple first-match. Future enhancements:
        - Load balancing (select least busy agent)
        - Priority-based selection
        - Capability scoring
    """
    for agent in agents:
        # Skip offline agents
        if agent.status != "online":
            continue
        
        # Check if agent has all required capabilities
        # capabilities is stored as JSON (dict) in the model
        agent_caps = agent.capabilities if isinstance(agent.capabilities, dict) else {}
        job_reqs = job.requirements if isinstance(job.requirements, list) else []
        
        if all(req in agent_caps for req in job_reqs):
            return agent
    
    return None


def match_job_to_mcp(
    job: Job, 
    services: list[MCPService]
) -> Optional[MCPService]:
    """Match a job to an available MCP service based on capabilities.
    
    Similar to match_job_to_agent but for MCP services.
    
    Args:
        job: The job to match
        services: List of registered MCP services
    
    Returns:
        The best matching service, or None if no match found
    """
    for service in services:
        # Skip offline services
        if service.status != "online":
            continue
        
        # Check if service has all required capabilities
        service_caps = service.capabilities if isinstance(service.capabilities, list) else []
        job_reqs = job.requirements if isinstance(job.requirements, list) else []
        
        if all(req in service_caps for req in job_reqs):
            return service
    
    return None


# TODO: Implement these for future enhancements
async def select_best_agent(agents: list[Agent]) -> Optional[Agent]:
    """Select the best agent from a list of candidates.
    
    Future enhancement: Load balancing based on:
    - Current job count per agent
    - Last heartbeat freshness
    - Historical performance metrics
    """
    raise NotImplementedError("Load balancing not yet implemented")


async def route_by_topic(topic: str, payload: dict) -> dict:
    """Route a message by topic (pub/sub pattern).
    
    Future enhancement: Topic-based routing for Kafka-like behavior.
    Services subscribe to topics, messages are broadcast.
    """
    raise NotImplementedError("Topic routing not yet implemented")
