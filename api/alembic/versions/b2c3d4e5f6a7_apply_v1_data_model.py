"""apply_v1_data_model

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-01-22

Applies the v1 Portfolio Data Model with:
- Security registry with equity and bond subtypes
- Transaction ledger (paper trades + cash flows)
- Current positions (cached/materialized)
- Data migration from legacy portfolios/holdings tables
- Integration with existing users table

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create v1 portfolio data model and migrate data."""

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
            coupon_rate NUMERIC(10, 6),
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
    # PORTFOLIO TABLE (with FK to users)
    # ===========================================

    op.execute("""
        CREATE TABLE portfolio (
            portfolio_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
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
    # TRANSACTION LEDGER (append-only)
    # ===========================================

    op.execute("""
        CREATE TABLE transaction_ledger (
            txn_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            portfolio_id UUID NOT NULL REFERENCES portfolio(portfolio_id) ON DELETE CASCADE,
            event_ts TIMESTAMPTZ NOT NULL DEFAULT now(),
            txn_type transaction_type NOT NULL,
            security_id UUID REFERENCES security_registry(security_id),
            quantity NUMERIC(18, 8) NOT NULL,
            price NUMERIC(18, 8),
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
            avg_cost NUMERIC(18, 8) NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            PRIMARY KEY (portfolio_id, security_id)
        )
    """)

    op.execute("""
        CREATE INDEX idx_position_current_portfolio_id ON position_current(portfolio_id)
    """)

    # ===========================================
    # CASH BALANCE (per portfolio per currency)
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

    # ===========================================
    # DATA MIGRATION
    # ===========================================

    # Step 1: Migrate portfolios -> portfolio
    op.execute("""
        INSERT INTO portfolio (portfolio_id, user_id, name, base_currency, created_at, updated_at)
        SELECT
            id as portfolio_id,
            user_id,
            name,
            'USD' as base_currency,
            created_at,
            updated_at
        FROM portfolios
    """)

    # Step 2: Create security_registry entries for unique securities from holdings
    # Map asset types: equity/etf/bond/mutual_fund -> EQUITY/ETF/BOND/EQUITY
    op.execute("""
        INSERT INTO security_registry (security_id, asset_type, currency, display_name, is_active, created_at, updated_at)
        SELECT
            gen_random_uuid() as security_id,
            CASE
                WHEN asset_type = 'equity' THEN 'EQUITY'::asset_type
                WHEN asset_type = 'etf' THEN 'ETF'::asset_type
                WHEN asset_type = 'bond' THEN 'BOND'::asset_type
                ELSE 'EQUITY'::asset_type
            END as asset_type,
            'USD' as currency,
            name as display_name,
            true as is_active,
            MIN(created_at) as created_at,
            MAX(created_at) as updated_at
        FROM holdings
        WHERE ticker IS NOT NULL
        GROUP BY ticker, name, asset_type
    """)

    # Step 3: Create equity_details for equity/etf/mutual_fund securities
    op.execute("""
        INSERT INTO equity_details (security_id, ticker, sector, industry, created_at, updated_at)
        SELECT DISTINCT ON (h.ticker)
            sr.security_id,
            h.ticker,
            NULLIF(h.sector, '') as sector,
            NULL as industry,
            sr.created_at,
            sr.updated_at
        FROM holdings h
        JOIN security_registry sr ON sr.display_name = h.name
        WHERE h.asset_type IN ('equity', 'etf', 'mutual_fund')
        ORDER BY h.ticker, h.created_at DESC
    """)

    # Step 4: Create security_identifier entries (primary ticker)
    op.execute("""
        INSERT INTO security_identifier (security_id, id_type, id_value, is_primary, created_at)
        SELECT
            ed.security_id,
            'TICKER'::identifier_type as id_type,
            ed.ticker as id_value,
            true as is_primary,
            ed.created_at
        FROM equity_details ed
    """)

    # Step 5: Create position_current entries
    op.execute("""
        INSERT INTO position_current (portfolio_id, security_id, quantity, avg_cost, updated_at)
        SELECT
            h.portfolio_id,
            sr.security_id,
            h.quantity,
            COALESCE(h.purchase_price, 0) as avg_cost,
            h.created_at as updated_at
        FROM holdings h
        JOIN security_registry sr ON sr.display_name = h.name
        WHERE h.portfolio_id IS NOT NULL AND h.quantity > 0
    """)

    # ===========================================
    # DROP LEGACY TABLES
    # ===========================================

    op.execute("DROP TABLE holdings")
    op.execute("DROP TABLE portfolios")


def downgrade() -> None:
    """Restore legacy tables and drop v1 tables."""

    # ===========================================
    # RECREATE LEGACY TABLES
    # ===========================================

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

    op.execute("""
        CREATE INDEX idx_portfolios_user_id ON portfolios(user_id)
    """)

    op.execute("""
        CREATE TABLE holdings (
            id UUID PRIMARY KEY,
            session_id UUID,
            ticker VARCHAR(20) NOT NULL,
            name VARCHAR(255) NOT NULL,
            asset_class VARCHAR(100) NOT NULL,
            sector VARCHAR(100) NOT NULL,
            broker VARCHAR(100) NOT NULL,
            purchase_date DATE NOT NULL,
            created_at TIMESTAMPTZ NOT NULL,
            portfolio_id UUID REFERENCES portfolios(id) ON DELETE CASCADE,
            asset_type VARCHAR(50) DEFAULT 'equity',
            quantity DECIMAL(18, 8) DEFAULT 0,
            purchase_price DECIMAL(18, 4) DEFAULT 0,
            current_price DECIMAL(18, 4)
        )
    """)

    op.execute("""
        CREATE INDEX idx_holdings_portfolio_id ON holdings(portfolio_id)
    """)

    # ===========================================
    # MIGRATE DATA BACK
    # ===========================================

    # Migrate portfolio -> portfolios
    op.execute("""
        INSERT INTO portfolios (id, user_id, name, description, created_at, updated_at)
        SELECT
            portfolio_id as id,
            user_id,
            name,
            NULL as description,
            created_at,
            updated_at
        FROM portfolio
    """)

    # Migrate position_current + equity_details -> holdings
    op.execute("""
        INSERT INTO holdings (id, ticker, name, asset_class, sector, broker, purchase_date, created_at, portfolio_id, asset_type, quantity, purchase_price)
        SELECT
            gen_random_uuid() as id,
            ed.ticker,
            sr.display_name as name,
            COALESCE(ed.sector, 'Unknown') as asset_class,
            COALESCE(ed.sector, 'Unknown') as sector,
            'Unknown' as broker,
            pc.updated_at::date as purchase_date,
            pc.updated_at as created_at,
            pc.portfolio_id,
            LOWER(sr.asset_type::text) as asset_type,
            pc.quantity,
            pc.avg_cost as purchase_price
        FROM position_current pc
        JOIN security_registry sr ON pc.security_id = sr.security_id
        LEFT JOIN equity_details ed ON sr.security_id = ed.security_id
    """)

    # ===========================================
    # DROP V1 TABLES
    # ===========================================

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
