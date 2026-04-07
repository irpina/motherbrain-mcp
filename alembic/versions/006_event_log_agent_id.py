"""Add agent_id to event_logs

Revision ID: 006
Revises: 005
Create Date: 2026-04-07

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add agent_id column to event_logs table."""
    op.add_column("event_logs", sa.Column("agent_id", sa.String(), nullable=True))


def downgrade() -> None:
    """Remove agent_id column from event_logs table."""
    op.drop_column("event_logs", "agent_id")
