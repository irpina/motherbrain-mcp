"""Add chat infrastructure and agent spawn tables

Revision ID: 014
Revises: 013_job_context_refs
Create Date: 2026-04-12
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '014_chat_and_agent_spawn'
down_revision = '013_job_context_refs'
branch_labels = None
depends_on = None


def upgrade():
    # Create channels table
    op.create_table(
        'channels',
        sa.Column('id', sa.String, primary_key=True),
        sa.Column('name', sa.String, unique=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False)
    )
    op.create_index('ix_channels_name', 'channels', ['name'])
    
    # Create chat_messages table
    op.create_table(
        'chat_messages',
        sa.Column('id', sa.Integer, autoincrement=True, primary_key=True),
        sa.Column('channel_id', sa.String, sa.ForeignKey('channels.id', ondelete='CASCADE'), nullable=False),
        sa.Column('sender', sa.String, nullable=False),
        sa.Column('text', sa.Text, nullable=False),
        sa.Column('type', sa.String, nullable=False, server_default='chat'),
        sa.Column('reply_to', sa.Integer, sa.ForeignKey('chat_messages.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False)
    )
    op.create_index('ix_chat_messages_channel_id', 'chat_messages', ['channel_id'])
    op.create_index('ix_chat_messages_sender', 'chat_messages', ['sender'])
    
    # Create agent_credentials table
    op.create_table(
        'agent_credentials',
        sa.Column('id', sa.String, primary_key=True),
        sa.Column('agent_type', sa.String, unique=True, nullable=False),
        sa.Column('api_key_encrypted', sa.LargeBinary, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False)
    )
    op.create_index('ix_agent_credentials_agent_type', 'agent_credentials', ['agent_type'])
    
    # Create spawned_agents table
    op.create_table(
        'spawned_agents',
        sa.Column('id', sa.String, primary_key=True),
        sa.Column('agent_type', sa.String, nullable=False),
        sa.Column('container_id', sa.String, unique=True, nullable=False),
        sa.Column('channel', sa.String, nullable=False),
        sa.Column('status', sa.String, nullable=False, server_default='running'),
        sa.Column('task', sa.String, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('stopped_at', sa.DateTime(timezone=True), nullable=True)
    )
    op.create_index('ix_spawned_agents_agent_type', 'spawned_agents', ['agent_type'])


def downgrade():
    op.drop_table('spawned_agents')
    op.drop_table('agent_credentials')
    op.drop_table('chat_messages')
    op.drop_table('channels')
