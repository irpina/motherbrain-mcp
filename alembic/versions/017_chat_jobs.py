"""Add chat_jobs table for agent job coordination

Revision ID: 017
Revises: 016_channel_private
Create Date: 2026-04-13
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '017_chat_jobs'
down_revision = '016_channel_private'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'chat_jobs',
        sa.Column('id', sa.String, primary_key=True),
        sa.Column('title', sa.String, nullable=False),
        sa.Column('body', sa.Text, nullable=False),
        sa.Column('category', sa.String, nullable=False, server_default='general'),
        sa.Column('channel', sa.String, nullable=False, index=True),
        sa.Column('status', sa.String, nullable=False, server_default='open'),
        sa.Column('claimed_by', sa.String, nullable=True),
        sa.Column('created_by', sa.String, nullable=False),
        sa.Column('summary', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False)
    )
    op.create_index('ix_chat_jobs_status', 'chat_jobs', ['status'])
    op.create_index('ix_chat_jobs_category', 'chat_jobs', ['category'])


def downgrade():
    op.drop_table('chat_jobs')
