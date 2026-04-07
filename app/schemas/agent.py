from datetime import datetime
from pydantic import BaseModel, ConfigDict


class AgentCreate(BaseModel):
    name: str | None = None
    hostname: str | None = None
    platform: str
    capabilities: dict


class AgentResponse(BaseModel):
    agent_id: str
    name: str | None = None
    hostname: str | None = None
    platform: str
    capabilities: dict
    status: str
    presence: str
    last_heartbeat: datetime
    # Token is only returned on registration
    model_config = ConfigDict(from_attributes=True)


class AgentRegistrationResponse(BaseModel):
    agent_id: str
    name: str | None = None
    hostname: str | None = None
    platform: str
    capabilities: dict
    status: str
    presence: str
    last_heartbeat: datetime
    token: str
    model_config = ConfigDict(from_attributes=True)


class AgentStatusUpdate(BaseModel):
    status: str  # "online" | "offline" | "busy"
