from uuid import UUID, uuid4

from adapters.postgres.connection import PostgresConnectionPool
from domain.models.security import Security
from domain.ports.ticker_repository import TickerRepository, UserAddedTicker
from domain.ports.ticker_validator import ValidatedTicker


class PostgresTickerRepository(TickerRepository):
    """PostgreSQL implementation of TickerRepository."""

    def __init__(self, pool: PostgresConnectionPool) -> None:
        self._pool = pool

    def ticker_exists(self, ticker: str) -> bool:
        """Check if ticker exists in equity_details."""
        with self._pool.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM equity_details WHERE UPPER(ticker) = %s", (ticker.upper(),)
            )
            return cur.fetchone() is not None

    def add_security(self, validated: ValidatedTicker) -> UUID:
        """Insert into security_registry, equity_details, and security_identifier."""
        security_id = uuid4()

        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                # 1. Insert into security_registry
                cur.execute(
                    """
                    INSERT INTO security_registry (security_id, asset_type, currency, display_name)
                    VALUES (%s, %s::asset_type, %s, %s)
                    """,
                    (
                        str(security_id),
                        validated.asset_type,
                        validated.currency,
                        validated.display_name,
                    ),
                )

                # 2. Insert into equity_details
                cur.execute(
                    """
                    INSERT INTO equity_details (security_id, ticker, exchange, sector, industry)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        str(security_id),
                        validated.ticker,
                        validated.exchange,
                        validated.sector,
                        validated.industry,
                    ),
                )

                # 3. Insert into security_identifier (source='user' is default)
                cur.execute(
                    """
                    INSERT INTO security_identifier (security_id, id_type, id_value, is_primary)
                    VALUES (%s, 'TICKER'::identifier_type, %s, true)
                    """,
                    (str(security_id), validated.ticker),
                )

            conn.commit()
        return security_id

    def get_user_added_tickers(self) -> list[UserAddedTicker]:
        """Get all tickers added by users (source='user')."""
        with self._pool.cursor() as cur:
            cur.execute(
                """
                SELECT ed.ticker, sr.display_name, sr.asset_type::text, si.created_at
                FROM security_identifier si
                JOIN security_registry sr ON si.security_id = sr.security_id
                JOIN equity_details ed ON sr.security_id = ed.security_id
                WHERE si.source = 'user'
                ORDER BY si.created_at DESC
                """
            )
            rows = cur.fetchall()

        return [
            UserAddedTicker(
                ticker=row[0],
                display_name=row[1],
                asset_type=row[2],
                added_at=row[3],
            )
            for row in rows
        ]

    def get_all_securities(self) -> list[Security]:
        """Get all securities from the registry with their equity details."""
        with self._pool.cursor() as cur:
            cur.execute(
                """
                SELECT
                    sr.security_id,
                    ed.ticker,
                    sr.display_name,
                    sr.asset_type::text,
                    sr.currency,
                    ed.sector,
                    ed.industry,
                    ed.exchange
                FROM security_registry sr
                JOIN equity_details ed ON sr.security_id = ed.security_id
                WHERE sr.is_active = true
                ORDER BY ed.ticker
                """
            )
            rows = cur.fetchall()

        return [
            Security(
                security_id=row[0],
                ticker=row[1],
                display_name=row[2],
                asset_type=row[3],
                currency=row[4],
                sector=row[5],
                industry=row[6],
                exchange=row[7],
            )
            for row in rows
        ]

    def get_security_id_by_ticker(self, ticker: str) -> UUID | None:
        """Look up security_id by ticker symbol."""
        with self._pool.cursor() as cur:
            cur.execute(
                """
                SELECT sr.security_id
                FROM security_registry sr
                JOIN equity_details ed ON sr.security_id = ed.security_id
                WHERE UPPER(ed.ticker) = %s
                """,
                (ticker.upper(),),
            )
            row = cur.fetchone()
        return row[0] if row else None
