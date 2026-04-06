"""Add target_service_id to jobs

Revision ID: 003
Revises: 002
Create Date: 2026-04-06

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add target_service_id column to jobs table."""
    op.add_column(
        "jobs",
        sa.Column("target_service_id", sa.String(), nullable=True)
    )


def downgrade() -> None:
    """Remove target_service_id column from jobs table."""
    op.drop_column("jobs", "target_service_id")
