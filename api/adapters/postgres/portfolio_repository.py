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
                INSERT INTO portfolios (id, user_id, name, description, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id, user_id, name, description, created_at, updated_at
                """,
                (
                    portfolio.id,
                    portfolio.user_id,
                    portfolio.name,
                    portfolio.description,
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
                SELECT id, user_id, name, description, created_at, updated_at
                FROM portfolios
                WHERE id = %s
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
                SELECT id, user_id, name, description, created_at, updated_at
                FROM portfolios
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
                UPDATE portfolios
                SET name = %s,
                    description = %s,
                    updated_at = %s
                WHERE id = %s
                RETURNING id, user_id, name, description, created_at, updated_at
                """,
                (
                    portfolio.name,
                    portfolio.description,
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
                DELETE FROM portfolios
                WHERE id = %s
                """,
                (id,),
            )

    def get_all_with_users(self) -> list[tuple[Portfolio, str]]:
        """Retrieve all portfolios with owner email."""
        with self._pool.cursor() as cur:
            cur.execute(
                """
                SELECT p.id, p.user_id, p.name, p.description, p.created_at, p.updated_at, u.email
                FROM portfolios p
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
            description=row[3],
            created_at=row[4],
            updated_at=row[5],
        )
