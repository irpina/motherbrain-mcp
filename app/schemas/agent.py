from datetime import datetime
from pydantic import BaseModel, ConfigDict


class AgentCreate(BaseModel):
    platform: str
    capabilities: dict


class AgentResponse(BaseModel):
    agent_id: str
    platform: str
    capabilities: dict
    status: str
    last_heartbeat: datetime
    # Token is only returned on registration
    model_config = ConfigDict(from_attributes=True)


class AgentRegistrationResponse(BaseModel):
    agent_id: str
    platform: str
    capabilities: dict
    status: str
    last_heartbeat: datetime
    token: str
    model_config = ConfigDict(from_attributes=True)


class AgentStatusUpdate(BaseModel):
    status: str  # "online" | "offline" | "busy"
