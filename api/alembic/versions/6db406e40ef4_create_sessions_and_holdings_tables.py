"""create_sessions_and_holdings_tables

Revision ID: 6db406e40ef4
Revises: 
Create Date: 2026-01-10 19:24:41.224164

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6db406e40ef4'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create sessions table
    op.execute("""
        CREATE TABLE sessions (
            id UUID PRIMARY KEY,
            created_at TIMESTAMPTZ NOT NULL,
            last_accessed_at TIMESTAMPTZ NOT NULL
        )
    """)

    # Create holdings table
    op.execute("""
        CREATE TABLE holdings (
            id UUID PRIMARY KEY,
            session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
            ticker VARCHAR(20) NOT NULL,
            name VARCHAR(255) NOT NULL,
            asset_class VARCHAR(100) NOT NULL,
            sector VARCHAR(100) NOT NULL,
            broker VARCHAR(100) NOT NULL,
            purchase_date DATE NOT NULL,
            created_at TIMESTAMPTZ NOT NULL
        )
    """)

    # Create index on holdings.session_id
    op.execute("""
        CREATE INDEX idx_holdings_session_id ON holdings(session_id)
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop index first
    op.execute("DROP INDEX IF EXISTS idx_holdings_session_id")

    # Drop tables (holdings first due to foreign key)
    op.execute("DROP TABLE IF EXISTS holdings")
    op.execute("DROP TABLE IF EXISTS sessions")
