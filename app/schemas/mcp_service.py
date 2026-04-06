from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class MCPServiceCreate(BaseModel):
    service_id: str
    name: str
    endpoint: str
    capabilities: list[str] = []
    api_key: Optional[str] = None  # Optional API key for service auth


class MCPServiceHeartbeat(BaseModel):
    service_id: str


class MCPServiceResponse(BaseModel):
    service_id: str
    name: str
    endpoint: str
    capabilities: list[str]
    status: str
    last_heartbeat: Optional[datetime]
    model_config = ConfigDict(from_attributes=True)


class MCPServiceUpdate(BaseModel):
    name: Optional[str] = None
    endpoint: Optional[str] = None
    capabilities: Optional[list[str]] = None
