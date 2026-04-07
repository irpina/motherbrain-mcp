"""Agent Registry — In-memory agent tracking and trigger queue.

This module provides:
- Agent registry: Tracks which agents are online via heartbeats
- Trigger queue: Pending triggers waiting to be delivered to agents

Used by the heartbeat system to enable push-like delivery to agents
connected via Motherbrain MCP.
"""

from datetime import datetime, timezone
from collections import defaultdict
from typing import Any

# { agent_name: datetime } — last heartbeat time (UTC)
agent_registry: dict[str, datetime] = {}

# { agent_name: [trigger, ...] } — pending triggers waiting for delivery
trigger_queue: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)


def register_heartbeat(agent_name: str) -> None:
    """Record a heartbeat from an agent.
    
    Args:
        agent_name: The unique name of the agent checking in
    """
    agent_registry[agent_name] = datetime.now(timezone.utc)


def get_pending_triggers(agent_name: str) -> list[dict[str, Any]]:
    """Get and clear all pending triggers for an agent.
    
    Args:
        agent_name: The agent to fetch triggers for
        
    Returns:
        List of pending triggers (empty if none)
    """
    triggers = trigger_queue.get(agent_name, [])
    if triggers:
        trigger_queue[agent_name] = []
    return triggers


def enqueue_trigger(agent_name: str, trigger: dict[str, Any]) -> None:
    """Queue a trigger for delivery to an agent.
    
    Args:
        agent_name: The target agent name
        trigger: The trigger payload to deliver
    """
    trigger_queue[agent_name].append(trigger)


def is_agent_registered(agent_name: str) -> bool:
    """Check if an agent has ever heartbeated.
    
    Args:
        agent_name: The agent to check
        
    Returns:
        True if agent has registered via heartbeat
    """
    return agent_name in agent_registry


def get_agent_last_seen(agent_name: str) -> datetime | None:
    """Get when an agent last checked in.
    
    Args:
        agent_name: The agent to check
        
    Returns:
        Last heartbeat datetime or None if never seen
    """
    return agent_registry.get(agent_name)
