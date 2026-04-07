"""Add event_logs table for persistent event storage

Revision ID: 004
Revises: 003
Create Date: 2026-04-07

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create event_logs table for persistent event storage."""
    op.create_table(
        "event_logs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("event_id", sa.String(), nullable=False),
        sa.Column("topic", sa.String(), nullable=False),
        sa.Column("service_id", sa.String(), nullable=True),
        sa.Column("tool_name", sa.String(), nullable=False),
        sa.Column("arguments", sa.JSON(), nullable=False),
        sa.Column("response", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("duration_ms", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id")
    )
    
    # Create indexes for common query patterns
    op.create_index("ix_event_logs_topic", "event_logs", ["topic"])
    op.create_index("ix_event_logs_service_id", "event_logs", ["service_id"])
    op.create_index("ix_event_logs_created_at", "event_logs", ["created_at"])


def downgrade() -> None:
    """Drop event_logs table."""
    op.drop_index("ix_event_logs_created_at", table_name="event_logs")
    op.drop_index("ix_event_logs_service_id", table_name="event_logs")
    op.drop_index("ix_event_logs_topic", table_name="event_logs")
    op.drop_table("event_logs")
