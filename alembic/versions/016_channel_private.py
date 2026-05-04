"""Add private and created_by fields to channels

Revision ID: 016
Revises: 015_chat_hop
Create Date: 2026-04-13
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '016_channel_private'
down_revision = '015_chat_hop'
branch_labels = None
depends_on = None


def upgrade():
    # Add private field to channels table
    op.add_column(
        'channels',
        sa.Column('private', sa.Boolean, nullable=False, server_default='false')
    )
    op.add_column(
        'channels',
        sa.Column('created_by', sa.String, nullable=True)
    )


def downgrade():
    op.drop_column('channels', 'created_by')
    op.drop_column('channels', 'private')
