"""migrate_to_position_model

Revision ID: h5ee8d5d4c06
Revises: g4dd7c4c3b95
Create Date: 2026-02-02 12:00:00.000000

This migration:
1. Creates synthetic BUY transactions from existing positions
2. Removes holding compat columns from position_current table

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'h5ee8d5d4c06'
down_revision: Union[str, Sequence[str], None] = 'g4dd7c4c3b95'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Migrate existing positions to transaction-based model."""

    # Create synthetic BUY transactions from existing positions
    # This ensures the transaction ledger has the source of truth
    op.execute("""
        INSERT INTO transaction_ledger (
            txn_id, portfolio_id, event_ts, txn_type, security_id,
            quantity, price, fees, currency, notes
        )
        SELECT
            gen_random_uuid(),
            portfolio_id,
            updated_at,
            'BUY'::transaction_type,
            security_id,
            quantity,
            avg_cost,
            0,
            'USD',
            'Migrated from position_current'
        FROM position_current
        WHERE quantity > 0
        AND NOT EXISTS (
            SELECT 1 FROM transaction_ledger tl
            WHERE tl.portfolio_id = position_current.portfolio_id
            AND tl.security_id = position_current.security_id
        )
    """)

    # Remove holding compat columns from position_current
    op.execute("""
        ALTER TABLE position_current
        DROP COLUMN IF EXISTS broker,
        DROP COLUMN IF EXISTS purchase_date,
        DROP COLUMN IF EXISTS current_price,
        DROP COLUMN IF EXISTS asset_class
    """)


def downgrade() -> None:
    """Restore holding compat columns."""

    # Add back the compat columns
    op.execute("""
        ALTER TABLE position_current
        ADD COLUMN IF NOT EXISTS broker VARCHAR(100) DEFAULT 'Unknown',
        ADD COLUMN IF NOT EXISTS purchase_date DATE DEFAULT CURRENT_DATE,
        ADD COLUMN IF NOT EXISTS current_price NUMERIC(18, 8),
        ADD COLUMN IF NOT EXISTS asset_class VARCHAR(100) DEFAULT 'Unknown'
    """)

    # Note: We don't delete the synthetic transactions as they are valid audit trail
