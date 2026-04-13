from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class ProjectContextCreate(BaseModel):
    value: dict
    updated_by: str
    description: Optional[str] = None
    service_id: Optional[str] = None
    category: Optional[str] = None


class ProjectContextUpdate(BaseModel):
    value: dict
    updated_by: str
    description: Optional[str] = None
    service_id: Optional[str] = None
    category: Optional[str] = None


class ProjectContextResponse(BaseModel):
    context_key: str
    value: dict
    last_updated: datetime
    updated_by: str
    description: Optional[str]
    service_id: Optional[str]
    category: Optional[str]
    model_config = ConfigDict(from_attributes=True)
