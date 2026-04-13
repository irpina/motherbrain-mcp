"""Add context job references and skill key to jobs

Revision ID: 013
Revises: 012_context_rbac
Create Date: 2026-04-09
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '013_job_context_refs'
down_revision = '012_context_rbac'
branch_labels = None
depends_on = None


def upgrade():
    # Add context_job_ids column for referencing prior jobs
    op.add_column(
        'jobs',
        sa.Column('context_job_ids', sa.JSON, nullable=False, server_default='[]')
    )
    
    # Add skill_key column for referencing context/skills store
    op.add_column(
        'jobs',
        sa.Column('skill_key', sa.String, nullable=True)
    )
    op.create_index('ix_jobs_skill_key', 'jobs', ['skill_key'])


def downgrade():
    op.drop_index('ix_jobs_skill_key')
    op.drop_column('jobs', 'skill_key')
    op.drop_column('jobs', 'context_job_ids')
