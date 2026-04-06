from datetime import datetime
from pydantic import BaseModel, ConfigDict


class AgentMessageCreate(BaseModel):
    sender_id: str
    recipient_id: str
    content: str
    message_type: str = "text"
    priority: str = "normal"


class AgentMessageResponse(BaseModel):
    message_id: str
    sender_id: str
    recipient_id: str
    content: str
    message_type: str
    priority: str
    timestamp: datetime
    delivered: bool
    read: bool
    model_config = ConfigDict(from_attributes=True)


class AgentMessageUpdate(BaseModel):
    delivered: bool = True
    read: bool = True
