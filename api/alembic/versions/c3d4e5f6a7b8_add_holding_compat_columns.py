"""add_holding_compat_columns

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-01-22

Add compatibility columns to position_current for holding API support.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add holding compatibility columns to position_current."""
    op.execute("""
        ALTER TABLE position_current
        ADD COLUMN broker VARCHAR(100) NOT NULL DEFAULT 'Unknown',
        ADD COLUMN purchase_date DATE NOT NULL DEFAULT CURRENT_DATE,
        ADD COLUMN current_price NUMERIC(18, 8),
        ADD COLUMN asset_class VARCHAR(100) NOT NULL DEFAULT 'Unknown'
    """)

    # Update existing positions with sector as asset_class where available
    op.execute("""
        UPDATE position_current pc
        SET asset_class = COALESCE(ed.sector, 'Unknown')
        FROM equity_details ed
        WHERE pc.security_id = ed.security_id
    """)


def downgrade() -> None:
    """Remove holding compatibility columns from position_current."""
    op.execute("""
        ALTER TABLE position_current
        DROP COLUMN IF EXISTS broker,
        DROP COLUMN IF EXISTS purchase_date,
        DROP COLUMN IF EXISTS current_price,
        DROP COLUMN IF EXISTS asset_class
    """)
