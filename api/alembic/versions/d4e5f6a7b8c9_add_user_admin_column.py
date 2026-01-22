"""add_user_admin_column

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-01-22

Add is_admin column to users table for admin access control.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, Sequence[str], None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add is_admin column to users table."""
    op.execute("""
        ALTER TABLE users
        ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT false
    """)

    # Make debug-test@example.com an admin
    op.execute("""
        UPDATE users
        SET is_admin = true
        WHERE email = 'debug-test@example.com'
    """)


def downgrade() -> None:
    """Remove is_admin column from users table."""
    op.execute("""
        ALTER TABLE users
        DROP COLUMN IF EXISTS is_admin
    """)
