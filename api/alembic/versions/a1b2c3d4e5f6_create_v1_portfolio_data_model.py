"""create_v1_portfolio_data_model

Revision ID: a1b2c3d4e5f6
Revises: db5e0b663db5
Create Date: 2026-01-14

Implements the v1 Portfolio Data Model with support for:
- Portfolio/account ownership
- Security registry with equity and bond subtypes
- Transaction ledger (paper trades + cash flows)
- Current positions (cached/materialized)

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'db5e0b663db5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create v1 portfolio data model tables."""

    # ===========================================
    # ENUM TYPES
    # ===========================================

    op.execute("""
        CREATE TYPE asset_type AS ENUM ('EQUITY', 'ETF', 'BOND', 'CASH')
    """)

    op.execute("""
        CREATE TYPE identifier_type AS ENUM ('TICKER', 'CUSIP', 'ISIN')
    """)

    op.execute("""
        CREATE TYPE coupon_type AS ENUM ('FIXED', 'ZERO')
    """)

    op.execute("""
        CREATE TYPE payment_frequency AS ENUM ('ANNUAL', 'SEMIANNUAL', 'QUARTERLY', 'MONTHLY')
    """)

    op.execute("""
        CREATE TYPE day_count_convention AS ENUM ('30_360', 'ACT_360', 'ACT_365', 'ACT_ACT')
    """)

    op.execute("""
        CREATE TYPE price_quote_convention AS ENUM ('CLEAN_PERCENT_OF_PAR')
    """)

    op.execute("""
        CREATE TYPE transaction_type AS ENUM (
            'BUY', 'SELL', 'DEPOSIT', 'WITHDRAW', 'FEE', 'DIVIDEND', 'COUPON'
        )
    """)

    # ===========================================
    # PORTFOLIO TABLE
    # ===========================================

    op.execute("""
        CREATE TABLE portfolio (
            portfolio_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL,
            name VARCHAR(255) NOT NULL,
            base_currency VARCHAR(3) NOT NULL DEFAULT 'USD',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)

    op.execute("""
        CREATE INDEX idx_portfolio_user_id ON portfolio(user_id)
    """)

    # ===========================================
    # SECURITY REGISTRY (canonical instrument identity)
    # ===========================================

    op.execute("""
        CREATE TABLE security_registry (
            security_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            asset_type asset_type NOT NULL,
            currency VARCHAR(3) NOT NULL DEFAULT 'USD',
            display_name VARCHAR(255) NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)

    op.execute("""
        CREATE INDEX idx_security_registry_asset_type ON security_registry(asset_type)
    """)

    # ===========================================
    # SECURITY IDENTIFIER (multiple identifiers per security)
    # ===========================================

    op.execute("""
        CREATE TABLE security_identifier (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            security_id UUID NOT NULL REFERENCES security_registry(security_id) ON DELETE CASCADE,
            id_type identifier_type NOT NULL,
            id_value VARCHAR(50) NOT NULL,
            source VARCHAR(100) NOT NULL DEFAULT 'user',
            is_primary BOOLEAN NOT NULL DEFAULT false,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE (id_type, id_value)
        )
    """)

    op.execute("""
        CREATE INDEX idx_security_identifier_security_id ON security_identifier(security_id)
    """)

    op.execute("""
        CREATE INDEX idx_security_identifier_lookup ON security_identifier(id_type, id_value)
    """)

    # ===========================================
    # EQUITY DETAILS (subtype)
    # ===========================================

    op.execute("""
        CREATE TABLE equity_details (
            security_id UUID PRIMARY KEY REFERENCES security_registry(security_id) ON DELETE CASCADE,
            ticker VARCHAR(20) NOT NULL,
            exchange VARCHAR(50),
            country VARCHAR(3),
            sector VARCHAR(100),
            industry VARCHAR(100),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)

    op.execute("""
        CREATE INDEX idx_equity_details_ticker ON equity_details(ticker)
    """)

    # ===========================================
    # BOND DETAILS (subtype) - v1: fixed and zero coupon only
    # ===========================================

    op.execute("""
        CREATE TABLE bond_details (
            security_id UUID PRIMARY KEY REFERENCES security_registry(security_id) ON DELETE CASCADE,
            issuer_name VARCHAR(255) NOT NULL,
            coupon_type coupon_type NOT NULL,
            coupon_rate NUMERIC(10, 6),  -- nullable for ZERO coupon
            payment_frequency payment_frequency NOT NULL,
            day_count_convention day_count_convention NOT NULL,
            issue_date DATE NOT NULL,
            maturity_date DATE NOT NULL,
            par_value NUMERIC(18, 6) NOT NULL DEFAULT 100.00,
            price_quote_convention price_quote_convention NOT NULL DEFAULT 'CLEAN_PERCENT_OF_PAR',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT chk_coupon_rate_for_fixed CHECK (
                (coupon_type = 'ZERO' AND coupon_rate IS NULL) OR
                (coupon_type = 'FIXED' AND coupon_rate IS NOT NULL AND coupon_rate >= 0)
            ),
            CONSTRAINT chk_maturity_after_issue CHECK (maturity_date > issue_date)
        )
    """)

    op.execute("""
        CREATE INDEX idx_bond_details_maturity ON bond_details(maturity_date)
    """)

    # ===========================================
    # TRANSACTION LEDGER (append-only)
    # ===========================================

    op.execute("""
        CREATE TABLE transaction_ledger (
            txn_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            portfolio_id UUID NOT NULL REFERENCES portfolio(portfolio_id) ON DELETE CASCADE,
            event_ts TIMESTAMPTZ NOT NULL DEFAULT now(),
            txn_type transaction_type NOT NULL,
            security_id UUID REFERENCES security_registry(security_id),  -- nullable for pure cash events
            quantity NUMERIC(18, 8) NOT NULL,  -- shares, face_amount, or currency amount
            price NUMERIC(18, 8),  -- nullable for DEPOSIT/WITHDRAW/FEE; required for BUY/SELL
            fees NUMERIC(18, 8) NOT NULL DEFAULT 0,
            currency VARCHAR(3) NOT NULL DEFAULT 'USD',
            notes TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT chk_buy_sell_requires_security CHECK (
                txn_type NOT IN ('BUY', 'SELL') OR security_id IS NOT NULL
            ),
            CONSTRAINT chk_buy_sell_requires_price CHECK (
                txn_type NOT IN ('BUY', 'SELL') OR price IS NOT NULL
            ),
            CONSTRAINT chk_quantity_positive CHECK (quantity != 0)
        )
    """)

    op.execute("""
        CREATE INDEX idx_transaction_ledger_portfolio_id ON transaction_ledger(portfolio_id)
    """)

    op.execute("""
        CREATE INDEX idx_transaction_ledger_security_id ON transaction_ledger(security_id)
    """)

    op.execute("""
        CREATE INDEX idx_transaction_ledger_event_ts ON transaction_ledger(event_ts)
    """)

    op.execute("""
        CREATE INDEX idx_transaction_ledger_portfolio_event
        ON transaction_ledger(portfolio_id, event_ts)
    """)

    # ===========================================
    # POSITION CURRENT (materialized/cached)
    # ===========================================

    op.execute("""
        CREATE TABLE position_current (
            portfolio_id UUID NOT NULL REFERENCES portfolio(portfolio_id) ON DELETE CASCADE,
            security_id UUID NOT NULL REFERENCES security_registry(security_id) ON DELETE CASCADE,
            quantity NUMERIC(18, 8) NOT NULL,
            avg_cost NUMERIC(18, 8) NOT NULL,  -- simple average cost in trade currency
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            PRIMARY KEY (portfolio_id, security_id)
        )
    """)

    op.execute("""
        CREATE INDEX idx_position_current_portfolio_id ON position_current(portfolio_id)
    """)

    # ===========================================
    # CASH BALANCE (per portfolio per currency)
    # Pure currency approach: no security_id for cash
    # ===========================================

    op.execute("""
        CREATE TABLE cash_balance (
            portfolio_id UUID NOT NULL REFERENCES portfolio(portfolio_id) ON DELETE CASCADE,
            currency VARCHAR(3) NOT NULL,
            balance NUMERIC(18, 8) NOT NULL DEFAULT 0,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            PRIMARY KEY (portfolio_id, currency)
        )
    """)

    # ===========================================
    # UPDATE TRIGGER for updated_at columns
    # ===========================================

    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ language 'plpgsql'
    """)

    for table in ['portfolio', 'security_registry', 'equity_details', 'bond_details', 'position_current', 'cash_balance']:
        op.execute(f"""
            CREATE TRIGGER update_{table}_updated_at
            BEFORE UPDATE ON {table}
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()
        """)


def downgrade() -> None:
    """Drop v1 portfolio data model tables."""

    # Drop triggers
    for table in ['portfolio', 'security_registry', 'equity_details', 'bond_details', 'position_current', 'cash_balance']:
        op.execute(f"DROP TRIGGER IF EXISTS update_{table}_updated_at ON {table}")

    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column()")

    # Drop tables in reverse dependency order
    op.execute("DROP TABLE IF EXISTS cash_balance")
    op.execute("DROP TABLE IF EXISTS position_current")
    op.execute("DROP TABLE IF EXISTS transaction_ledger")
    op.execute("DROP TABLE IF EXISTS bond_details")
    op.execute("DROP TABLE IF EXISTS equity_details")
    op.execute("DROP TABLE IF EXISTS security_identifier")
    op.execute("DROP TABLE IF EXISTS security_registry")
    op.execute("DROP TABLE IF EXISTS portfolio")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS transaction_type")
    op.execute("DROP TYPE IF EXISTS price_quote_convention")
    op.execute("DROP TYPE IF EXISTS day_count_convention")
    op.execute("DROP TYPE IF EXISTS payment_frequency")
    op.execute("DROP TYPE IF EXISTS coupon_type")
    op.execute("DROP TYPE IF EXISTS identifier_type")
    op.execute("DROP TYPE IF EXISTS asset_type")
