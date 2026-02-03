from datetime import datetime, timezone
from uuid import UUID

from domain.ports.portfolio_builder_repository import (
    PortfolioBuilderRepository,
    PositionInput,
    SecurityInput,
    TransactionInput,
)
from domain.ports.unit_of_work import TransactionContext


class PostgresPortfolioBuilderRepository(PortfolioBuilderRepository):
    """Postgres implementation of PortfolioBuilderRepository."""

    def create_portfolio_in_transaction(
        self,
        ctx: TransactionContext,
        portfolio_id: UUID,
        user_id: UUID,
        name: str,
        base_currency: str,
    ) -> tuple:
        """Create a portfolio within a transaction context."""
        now = datetime.now(timezone.utc)
        ctx.execute(
            """
            INSERT INTO portfolio (portfolio_id, user_id, name, base_currency, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING portfolio_id, user_id, name, base_currency, created_at, updated_at
            """,
            (portfolio_id, user_id, name, base_currency, now, now),
        )
        row = ctx.fetchone()
        if row is None:
            raise RuntimeError("Failed to create portfolio")
        return row

    def find_security_by_ticker(
        self,
        ctx: TransactionContext,
        ticker: str,
    ) -> UUID | None:
        """Find a security by ticker within a transaction context."""
        ctx.execute(
            """
            SELECT sr.security_id
            FROM security_registry sr
            JOIN equity_details ed ON sr.security_id = ed.security_id
            WHERE ed.ticker = %s
            """,
            (ticker,),
        )
        row = ctx.fetchone()
        return row[0] if row else None

    def create_security_in_transaction(
        self,
        ctx: TransactionContext,
        security_id: UUID,
        security: SecurityInput,
    ) -> None:
        """Create a new security with equity details and identifier within a transaction."""
        asset_type = security.asset_type.upper()
        if asset_type not in ("EQUITY", "ETF", "BOND", "CASH"):
            asset_type = "EQUITY"

        ctx.execute(
            """
            INSERT INTO security_registry (security_id, asset_type, currency, display_name, is_active)
            VALUES (%s, %s::asset_type, 'USD', %s, true)
            """,
            (security_id, asset_type, security.display_name),
        )

        ctx.execute(
            """
            INSERT INTO equity_details (security_id, ticker, sector)
            VALUES (%s, %s, %s)
            """,
            (security_id, security.ticker, security.sector),
        )

        ctx.execute(
            """
            INSERT INTO security_identifier (security_id, id_type, id_value, is_primary)
            VALUES (%s, 'TICKER'::identifier_type, %s, true)
            """,
            (security_id, security.ticker),
        )

    def create_position_in_transaction(
        self,
        ctx: TransactionContext,
        position: PositionInput,
    ) -> None:
        """Create a position within a transaction context."""
        ctx.execute(
            """
            INSERT INTO position_current (portfolio_id, security_id, quantity, avg_cost)
            VALUES (%s, %s, %s, %s)
            """,
            (
                position.portfolio_id,
                position.security_id,
                position.quantity,
                position.avg_cost,
            ),
        )

    def create_transaction_in_transaction(
        self,
        ctx: TransactionContext,
        transaction: TransactionInput,
    ) -> None:
        """Create a transaction record within a transaction context."""
        event_ts = datetime.combine(
            transaction.event_ts, datetime.min.time(), timezone.utc
        )
        ctx.execute(
            """
            INSERT INTO transaction_ledger (
                txn_id, portfolio_id, event_ts, txn_type,
                security_id, quantity, price, fees, currency
            )
            VALUES (%s, %s, %s, %s::transaction_type, %s, %s, %s, 0, 'USD')
            """,
            (
                transaction.txn_id,
                transaction.portfolio_id,
                event_ts,
                transaction.txn_type,
                transaction.security_id,
                transaction.quantity,
                transaction.price,
            ),
        )
