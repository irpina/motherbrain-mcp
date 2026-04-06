"""Add MCP routing and service registry

Revision ID: 001
Revises: 
Create Date: 2026-04-06

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create mcp_services table and add MCP routing columns to jobs."""
    
    # Create MCP services table
    op.create_table(
        'mcp_services',
        sa.Column('service_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('endpoint', sa.String(), nullable=False),
        sa.Column('capabilities', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('last_heartbeat', sa.DateTime(timezone=True), nullable=True),
        sa.Column('api_key_hash', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('service_id')
    )
    
    # Add MCP routing columns to jobs table
    op.add_column('jobs', sa.Column('target_type', sa.String(), nullable=True, server_default='agent'))
    op.add_column('jobs', sa.Column('result', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('jobs', sa.Column('error', sa.String(), nullable=True))
    op.add_column('jobs', sa.Column('topic', sa.String(), nullable=True))


def downgrade() -> None:
    """Remove MCP services table and routing columns from jobs."""
    
    # Drop columns from jobs
    op.drop_column('jobs', 'topic')
    op.drop_column('jobs', 'error')
    op.drop_column('jobs', 'result')
    op.drop_column('jobs', 'target_type')
    
    # Drop mcp_services table
    op.drop_table('mcp_services')
