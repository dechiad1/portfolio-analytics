"""add_oauth_fields

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-01-23

Add OAuth fields to users table for OAuth2 authentication.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, Sequence[str], None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add OAuth fields to users table."""
    op.execute("""
        ALTER TABLE users
        ADD COLUMN last_login TIMESTAMPTZ,
        ADD COLUMN oauth_provider VARCHAR(50),
        ADD COLUMN oauth_subject VARCHAR(255)
    """)

    op.execute("""
        CREATE INDEX idx_users_oauth_subject ON users(oauth_provider, oauth_subject)
    """)

    op.execute("""
        ALTER TABLE users ALTER COLUMN password_hash DROP NOT NULL
    """)


def downgrade() -> None:
    """Remove OAuth fields from users table."""
    op.execute("DROP INDEX IF EXISTS idx_users_oauth_subject")
    op.execute("""
        ALTER TABLE users
        DROP COLUMN IF EXISTS last_login,
        DROP COLUMN IF EXISTS oauth_provider,
        DROP COLUMN IF EXISTS oauth_subject
    """)
    op.execute("""
        ALTER TABLE users ALTER COLUMN password_hash SET NOT NULL
    """)
