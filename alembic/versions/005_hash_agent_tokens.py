"""Rename token to token_hash for secure storage

Revision ID: 005
Revises: 004
Create Date: 2026-04-07

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Rename token column to token_hash.
    
    Note: Existing tokens become invalid after migration.
    Agents must re-register to get new tokens.
    """
    op.alter_column("agents", "token", new_column_name="token_hash")


def downgrade() -> None:
    """Rename token_hash back to token."""
    op.alter_column("agents", "token_hash", new_column_name="token")
