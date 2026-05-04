"""Create rules table

Revision ID: 018
Revises: 017_chat_jobs
Create Date: 2026-04-12
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "018"
down_revision: Union[str, None] = "017_chat_jobs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "rules",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("text", sa.String(length=500), nullable=False),
        sa.Column("author", sa.String(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("epoch", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_rules_status"), "rules", ["status"], unique=False)
    op.create_index(op.f("ix_rules_author"), "rules", ["author"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_rules_author"), table_name="rules")
    op.drop_index(op.f("ix_rules_status"), table_name="rules")
    op.drop_table("rules")
