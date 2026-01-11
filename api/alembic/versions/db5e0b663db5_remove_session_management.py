"""remove_session_management

Revision ID: db5e0b663db5
Revises: 6db406e40ef4
Create Date: 2026-01-10 19:53:30.844630

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'db5e0b663db5'
down_revision: Union[str, Sequence[str], None] = '6db406e40ef4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop the foreign key constraint from holdings to sessions
    op.execute("ALTER TABLE holdings DROP CONSTRAINT IF EXISTS holdings_session_id_fkey")

    # Make session_id nullable
    op.execute("ALTER TABLE holdings ALTER COLUMN session_id DROP NOT NULL")

    # Drop the sessions table (no longer needed)
    op.execute("DROP TABLE IF EXISTS sessions")


def downgrade() -> None:
    """Downgrade schema."""
    # Recreate sessions table
    op.execute("""
        CREATE TABLE sessions (
            id UUID PRIMARY KEY,
            created_at TIMESTAMPTZ NOT NULL,
            last_accessed_at TIMESTAMPTZ NOT NULL
        )
    """)

    # Make session_id NOT NULL again
    op.execute("ALTER TABLE holdings ALTER COLUMN session_id SET NOT NULL")

    # Recreate the foreign key constraint
    op.execute("""
        ALTER TABLE holdings
        ADD CONSTRAINT holdings_session_id_fkey
        FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
    """)
