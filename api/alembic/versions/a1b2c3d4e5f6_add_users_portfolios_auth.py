"""add_users_portfolios_auth

Revision ID: a1b2c3d4e5f6
Revises: db5e0b663db5
Create Date: 2026-01-19 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'db5e0b663db5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create users table
    op.execute("""
        CREATE TABLE users (
            id UUID PRIMARY KEY,
            email VARCHAR(255) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            created_at TIMESTAMPTZ NOT NULL
        )
    """)

    # Create index on users.email
    op.execute("""
        CREATE INDEX idx_users_email ON users(email)
    """)

    # Create portfolios table
    op.execute("""
        CREATE TABLE portfolios (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            created_at TIMESTAMPTZ NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL
        )
    """)

    # Create index on portfolios.user_id
    op.execute("""
        CREATE INDEX idx_portfolios_user_id ON portfolios(user_id)
    """)

    # Add new columns to holdings table
    op.execute("""
        ALTER TABLE holdings
        ADD COLUMN portfolio_id UUID REFERENCES portfolios(id) ON DELETE CASCADE,
        ADD COLUMN asset_type VARCHAR(50) DEFAULT 'equity',
        ADD COLUMN quantity DECIMAL(18, 8) DEFAULT 0,
        ADD COLUMN purchase_price DECIMAL(18, 4) DEFAULT 0,
        ADD COLUMN current_price DECIMAL(18, 4)
    """)

    # Create index on holdings.portfolio_id
    op.execute("""
        CREATE INDEX idx_holdings_portfolio_id ON holdings(portfolio_id)
    """)

    # Drop the old session_id index if exists
    op.execute("""
        DROP INDEX IF EXISTS idx_holdings_session_id
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # Remove new columns from holdings
    op.execute("""
        ALTER TABLE holdings
        DROP COLUMN IF EXISTS portfolio_id,
        DROP COLUMN IF EXISTS asset_type,
        DROP COLUMN IF EXISTS quantity,
        DROP COLUMN IF EXISTS purchase_price,
        DROP COLUMN IF EXISTS current_price
    """)

    # Drop indexes
    op.execute("DROP INDEX IF EXISTS idx_holdings_portfolio_id")
    op.execute("DROP INDEX IF EXISTS idx_portfolios_user_id")
    op.execute("DROP INDEX IF EXISTS idx_users_email")

    # Drop tables
    op.execute("DROP TABLE IF EXISTS portfolios")
    op.execute("DROP TABLE IF EXISTS users")

    # Recreate old index
    op.execute("""
        CREATE INDEX idx_holdings_session_id ON holdings(session_id)
    """)
