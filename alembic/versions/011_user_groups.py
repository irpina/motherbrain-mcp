"""Add user_groups junction table for RBAC

Revision ID: 011
Revises: 010_groups
Create Date: 2026-04-08
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '011_user_groups'
down_revision = '010_groups'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'user_groups',
        sa.Column('user_id', sa.String, sa.ForeignKey('users.user_id', ondelete='CASCADE'), primary_key=True),
        sa.Column('group_id', sa.String, sa.ForeignKey('groups.group_id', ondelete='CASCADE'), primary_key=True),
    )
    # Create indexes for faster lookups
    op.create_index('ix_user_groups_user_id', 'user_groups', ['user_id'])
    op.create_index('ix_user_groups_group_id', 'user_groups', ['group_id'])


def downgrade():
    op.drop_index('ix_user_groups_group_id')
    op.drop_index('ix_user_groups_user_id')
    op.drop_table('user_groups')
