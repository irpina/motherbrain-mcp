from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class MCPService(Base):
    __tablename__ = "mcp_services"

    service_id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    endpoint: Mapped[str] = mapped_column(String, nullable=False)
    capabilities: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String, default="offline")  # "online" | "offline"
    last_heartbeat: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        nullable=True
    )
    api_key_hash: Mapped[Optional[str]] = mapped_column(String, nullable=True)
