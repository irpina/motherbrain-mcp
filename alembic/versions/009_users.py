"""Add users table for RBAC

Revision ID: 009
Revises: 008_agent_hostname
Create Date: 2026-04-08
"""
from alembic import op
import sqlalchemy as sa
from uuid import uuid4

# revision identifiers, used by Alembic.
revision = '009_users'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'users',
        sa.Column('user_id', sa.String, primary_key=True, default=lambda: str(uuid4())),
        sa.Column('name', sa.String, nullable=False),
        sa.Column('email', sa.String, unique=True, nullable=True),
        sa.Column('role', sa.String, nullable=False, server_default='user'),  # 'admin' | 'user'
        sa.Column('token_hash', sa.String, nullable=True),
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('entra_object_id', sa.String, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    # Create index on email for faster lookups
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    # Create index on token_hash for auth lookups
    op.create_index('ix_users_token_hash', 'users', ['token_hash'])


def downgrade():
    op.drop_index('ix_users_token_hash')
    op.drop_index('ix_users_email')
    op.drop_table('users')
