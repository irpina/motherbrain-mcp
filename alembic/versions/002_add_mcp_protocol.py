"""Add protocol field to mcp_services

Revision ID: 002
Revises: 001
Create Date: 2026-04-06

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add protocol column to mcp_services table."""
    op.add_column(
        "mcp_services",
        sa.Column("protocol", sa.String(), nullable=True, server_default="rest")
    )


def downgrade() -> None:
    """Remove protocol column from mcp_services table."""
    op.drop_column("mcp_services", "protocol")
