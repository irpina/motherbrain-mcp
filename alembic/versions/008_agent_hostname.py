"""Add hostname column and drop unique constraint on name

Revision ID: 008
Revises: 007
Create Date: 2026-04-07

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Drop unique constraint on name, add hostname column, create composite index."""
    # Drop unique constraint on name
    op.drop_index("ix_agents_name", table_name="agents")
    
    # Add hostname column
    op.add_column("agents", sa.Column("hostname", sa.String(), nullable=True))
    
    # Create composite index on (name, hostname) for re-registration lookup
    op.create_index("ix_agents_name_hostname", "agents", ["name", "hostname"])


def downgrade() -> None:
    """Restore unique constraint on name, remove hostname."""
    # Drop composite index
    op.drop_index("ix_agents_name_hostname", table_name="agents")
    
    # Remove hostname column
    op.drop_column("agents", "hostname")
    
    # Restore unique index on name
    op.create_index("ix_agents_name", "agents", ["name"], unique=True)
