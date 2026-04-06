from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class AgentActionCreate(BaseModel):
    agent_id: str
    action_type: str
    job_id: Optional[str] = None
    details: Optional[dict] = None


class AgentActionResponse(BaseModel):
    action_id: int
    agent_id: str
    action_type: str
    job_id: Optional[str]
    timestamp: datetime
    details: Optional[dict]
    model_config = ConfigDict(from_attributes=True)
