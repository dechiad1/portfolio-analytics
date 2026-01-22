from uuid import UUID

from domain.models.portfolio import Portfolio
from domain.ports.portfolio_repository import PortfolioRepository

from adapters.postgres.connection import PostgresConnectionPool


class PostgresPortfolioRepository(PortfolioRepository):
    """PostgreSQL implementation of PortfolioRepository."""

    def __init__(self, pool: PostgresConnectionPool) -> None:
        self._pool = pool

    def create(self, portfolio: Portfolio) -> Portfolio:
        """Persist a new portfolio."""
        with self._pool.cursor() as cur:
            cur.execute(
                """
                INSERT INTO portfolio (portfolio_id, user_id, name, base_currency, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING portfolio_id, user_id, name, base_currency, created_at, updated_at
                """,
                (
                    portfolio.id,
                    portfolio.user_id,
                    portfolio.name,
                    portfolio.base_currency,
                    portfolio.created_at,
                    portfolio.updated_at,
                ),
            )
            row = cur.fetchone()

        if row is None:
            raise RuntimeError("Failed to create portfolio")

        return self._row_to_portfolio(row)

    def get_by_id(self, id: UUID) -> Portfolio | None:
        """Retrieve a portfolio by ID."""
        with self._pool.cursor() as cur:
            cur.execute(
                """
                SELECT portfolio_id, user_id, name, base_currency, created_at, updated_at
                FROM portfolio
                WHERE portfolio_id = %s
                """,
                (id,),
            )
            row = cur.fetchone()

        if row is None:
            return None

        return self._row_to_portfolio(row)

    def get_by_user_id(self, user_id: UUID) -> list[Portfolio]:
        """Retrieve all portfolios for a user."""
        with self._pool.cursor() as cur:
            cur.execute(
                """
                SELECT portfolio_id, user_id, name, base_currency, created_at, updated_at
                FROM portfolio
                WHERE user_id = %s
                ORDER BY created_at DESC
                """,
                (user_id,),
            )
            rows = cur.fetchall()

        return [self._row_to_portfolio(row) for row in rows]

    def update(self, portfolio: Portfolio) -> Portfolio:
        """Update an existing portfolio."""
        with self._pool.cursor() as cur:
            cur.execute(
                """
                UPDATE portfolio
                SET name = %s,
                    base_currency = %s,
                    updated_at = %s
                WHERE portfolio_id = %s
                RETURNING portfolio_id, user_id, name, base_currency, created_at, updated_at
                """,
                (
                    portfolio.name,
                    portfolio.base_currency,
                    portfolio.updated_at,
                    portfolio.id,
                ),
            )
            row = cur.fetchone()

        if row is None:
            raise RuntimeError(f"Failed to update portfolio {portfolio.id}")

        return self._row_to_portfolio(row)

    def delete(self, id: UUID) -> None:
        """Delete a portfolio by ID."""
        with self._pool.cursor() as cur:
            cur.execute(
                """
                DELETE FROM portfolio
                WHERE portfolio_id = %s
                """,
                (id,),
            )

    def get_all_with_users(self) -> list[tuple[Portfolio, str]]:
        """Retrieve all portfolios with owner email."""
        with self._pool.cursor() as cur:
            cur.execute(
                """
                SELECT p.portfolio_id, p.user_id, p.name, p.base_currency, p.created_at, p.updated_at, u.email
                FROM portfolio p
                JOIN users u ON p.user_id = u.id
                ORDER BY p.created_at DESC
                """
            )
            rows = cur.fetchall()

        return [(self._row_to_portfolio(row[:6]), row[6]) for row in rows]

    def _row_to_portfolio(self, row: tuple) -> Portfolio:
        """Convert a database row to a Portfolio model."""
        return Portfolio(
            id=row[0],
            user_id=row[1],
            name=row[2],
            base_currency=row[3],
            created_at=row[4],
            updated_at=row[5],
        )
