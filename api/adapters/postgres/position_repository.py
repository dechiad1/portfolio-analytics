from decimal import Decimal
from uuid import UUID

from adapters.postgres.connection import PostgresConnectionPool
from domain.models.position import Position
from domain.models.security import Security
from domain.ports.position_repository import PositionRepository


class PostgresPositionRepository(PositionRepository):
    """PostgreSQL implementation of PositionRepository."""

    def __init__(self, pool: PostgresConnectionPool) -> None:
        self._pool = pool

    def get_by_portfolio_id(self, portfolio_id: UUID) -> list[Position]:
        """Retrieve all positions for a portfolio with enriched security data."""
        with self._pool.cursor() as cur:
            cur.execute(
                """
                SELECT
                    pc.portfolio_id,
                    pc.security_id,
                    pc.quantity,
                    pc.avg_cost,
                    pc.updated_at,
                    sr.display_name,
                    sr.asset_type::text,
                    sr.currency,
                    COALESCE(ed.ticker, 'UNKNOWN') as ticker,
                    ed.sector,
                    ed.industry,
                    ed.exchange
                FROM position_current pc
                JOIN security_registry sr ON pc.security_id = sr.security_id
                LEFT JOIN equity_details ed ON sr.security_id = ed.security_id
                WHERE pc.portfolio_id = %s
                ORDER BY pc.updated_at ASC
                """,
                (portfolio_id,),
            )
            rows = cur.fetchall()

        return [self._row_to_position(row) for row in rows]

    def get_by_portfolio_and_security(
        self, portfolio_id: UUID, security_id: UUID
    ) -> Position | None:
        """Retrieve a specific position with enriched security data."""
        with self._pool.cursor() as cur:
            cur.execute(
                """
                SELECT
                    pc.portfolio_id,
                    pc.security_id,
                    pc.quantity,
                    pc.avg_cost,
                    pc.updated_at,
                    sr.display_name,
                    sr.asset_type::text,
                    sr.currency,
                    COALESCE(ed.ticker, 'UNKNOWN') as ticker,
                    ed.sector,
                    ed.industry,
                    ed.exchange
                FROM position_current pc
                JOIN security_registry sr ON pc.security_id = sr.security_id
                LEFT JOIN equity_details ed ON sr.security_id = ed.security_id
                WHERE pc.portfolio_id = %s AND pc.security_id = %s
                """,
                (portfolio_id, security_id),
            )
            row = cur.fetchone()

        if row is None:
            return None

        return self._row_to_position(row)

    def upsert(self, position: Position) -> Position:
        """Create or update a position."""
        with self._pool.cursor() as cur:
            cur.execute(
                """
                INSERT INTO position_current (portfolio_id, security_id, quantity, avg_cost)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (portfolio_id, security_id)
                DO UPDATE SET
                    quantity = EXCLUDED.quantity,
                    avg_cost = EXCLUDED.avg_cost
                RETURNING portfolio_id, security_id, quantity, avg_cost, updated_at
                """,
                (
                    position.portfolio_id,
                    position.security_id,
                    position.quantity,
                    position.avg_cost,
                ),
            )
            row = cur.fetchone()

        if row is None:
            raise RuntimeError("Failed to upsert position")

        return Position(
            portfolio_id=row[0],
            security_id=row[1],
            quantity=Decimal(str(row[2])),
            avg_cost=Decimal(str(row[3])),
            updated_at=row[4],
        )

    def delete(self, portfolio_id: UUID, security_id: UUID) -> None:
        """Delete a position."""
        with self._pool.cursor() as cur:
            cur.execute(
                """
                DELETE FROM position_current
                WHERE portfolio_id = %s AND security_id = %s
                """,
                (portfolio_id, security_id),
            )

    def bulk_upsert(self, positions: list[Position]) -> list[Position]:
        """Create or update multiple positions."""
        if not positions:
            return []

        results = []
        for position in positions:
            results.append(self.upsert(position))
        return results

    def _row_to_position(self, row: tuple) -> Position:
        """Convert a database row to a Position model with Security."""
        security = Security(
            security_id=row[1],
            ticker=row[8] or "UNKNOWN",
            display_name=row[5],
            asset_type=row[6].lower() if row[6] else "equity",
            currency=row[7] or "USD",
            sector=row[9],
            industry=row[10],
            exchange=row[11],
        )

        return Position(
            portfolio_id=row[0],
            security_id=row[1],
            quantity=Decimal(str(row[2])) if row[2] else Decimal("0"),
            avg_cost=Decimal(str(row[3])) if row[3] else Decimal("0"),
            updated_at=row[4],
            security=security,
        )
