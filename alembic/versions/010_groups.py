"""Add groups table for RBAC

Revision ID: 010
Revises: 009_users
Create Date: 2026-04-08
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from uuid import uuid4

# revision identifiers, used by Alembic.
revision = '010_groups'
down_revision = '009_users'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'groups',
        sa.Column('group_id', sa.String, primary_key=True, default=lambda: str(uuid4())),
        sa.Column('name', sa.String, nullable=False, unique=True),
        sa.Column('description', sa.String, nullable=True),
        sa.Column('allowed_service_ids', postgresql.JSONB, server_default='[]'),
        sa.Column('entra_group_id', sa.String, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    # Create index on name for faster lookups
    op.create_index('ix_groups_name', 'groups', ['name'], unique=True)


def downgrade():
    op.drop_index('ix_groups_name')
    op.drop_table('groups')
