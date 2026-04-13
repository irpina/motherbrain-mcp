"""Add RBAC columns to project_context for skills

Revision ID: 012
Revises: 011_user_groups
Create Date: 2026-04-09
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '012_context_rbac'
down_revision = '011_user_groups'
branch_labels = None
depends_on = None


def upgrade():
    # Add service_id column for RBAC linking to MCP services
    op.add_column(
        'project_context',
        sa.Column('service_id', sa.String, nullable=True)
    )
    op.create_index('ix_project_context_service_id', 'project_context', ['service_id'])
    
    # Add category column for UI organization
    op.add_column(
        'project_context',
        sa.Column('category', sa.String, nullable=True)
    )
    op.create_index('ix_project_context_category', 'project_context', ['category'])


def downgrade():
    op.drop_index('ix_project_context_category')
    op.drop_index('ix_project_context_service_id')
    op.drop_column('project_context', 'category')
    op.drop_column('project_context', 'service_id')
