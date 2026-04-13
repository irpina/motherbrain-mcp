"""Add hop column to chat_messages for loop guard

Revision ID: 015
Revises: 014_chat_and_agent_spawn
Create Date: 2026-04-13
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '015_chat_hop'
down_revision = '014_chat_and_agent_spawn'
branch_labels = None
depends_on = None


def upgrade():
    # Add hop column to chat_messages table
    op.add_column(
        'chat_messages',
        sa.Column('hop', sa.Integer, nullable=False, server_default='0')
    )


def downgrade():
    op.drop_column('chat_messages', 'hop')
