from uuid import UUID

from psycopg import sql

from domain.models.holding import Holding
from domain.ports.holding_repository import HoldingRepository

from adapters.postgres.connection import PostgresConnectionPool


class PostgresHoldingRepository(HoldingRepository):
    """PostgreSQL implementation of HoldingRepository."""

    def __init__(self, pool: PostgresConnectionPool) -> None:
        self._pool = pool

    def create(self, holding: Holding) -> Holding:
        """Persist a new holding."""
        with self._pool.cursor() as cur:
            cur.execute(
                """
                INSERT INTO holdings (
                    id, session_id, ticker, name, asset_class,
                    sector, broker, purchase_date, created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, session_id, ticker, name, asset_class,
                          sector, broker, purchase_date, created_at
                """,
                (
                    holding.id,
                    holding.session_id,
                    holding.ticker,
                    holding.name,
                    holding.asset_class,
                    holding.sector,
                    holding.broker,
                    holding.purchase_date,
                    holding.created_at,
                ),
            )
            row = cur.fetchone()

        if row is None:
            raise RuntimeError("Failed to create holding")

        return self._row_to_holding(row)

    def get_by_id(self, id: UUID) -> Holding | None:
        """Retrieve a holding by its ID."""
        with self._pool.cursor() as cur:
            cur.execute(
                """
                SELECT id, session_id, ticker, name, asset_class,
                       sector, broker, purchase_date, created_at
                FROM holdings
                WHERE id = %s
                """,
                (id,),
            )
            row = cur.fetchone()

        if row is None:
            return None

        return self._row_to_holding(row)

    def get_by_session_id(self, session_id: UUID | None) -> list[Holding]:
        """Retrieve all holdings for a session. If session_id is None, return all holdings."""
        with self._pool.cursor() as cur:
            if session_id is None:
                cur.execute(
                    """
                    SELECT id, session_id, ticker, name, asset_class,
                           sector, broker, purchase_date, created_at
                    FROM holdings
                    ORDER BY created_at ASC
                    """
                )
            else:
                cur.execute(
                    """
                    SELECT id, session_id, ticker, name, asset_class,
                           sector, broker, purchase_date, created_at
                    FROM holdings
                    WHERE session_id = %s
                    ORDER BY created_at ASC
                    """,
                    (session_id,),
                )
            rows = cur.fetchall()

        return [self._row_to_holding(row) for row in rows]

    def update(self, holding: Holding) -> Holding:
        """Update an existing holding."""
        with self._pool.cursor() as cur:
            cur.execute(
                """
                UPDATE holdings
                SET ticker = %s,
                    name = %s,
                    asset_class = %s,
                    sector = %s,
                    broker = %s,
                    purchase_date = %s
                WHERE id = %s
                RETURNING id, session_id, ticker, name, asset_class,
                          sector, broker, purchase_date, created_at
                """,
                (
                    holding.ticker,
                    holding.name,
                    holding.asset_class,
                    holding.sector,
                    holding.broker,
                    holding.purchase_date,
                    holding.id,
                ),
            )
            row = cur.fetchone()

        if row is None:
            raise RuntimeError(f"Failed to update holding {holding.id}")

        return self._row_to_holding(row)

    def delete(self, id: UUID) -> None:
        """Delete a holding by its ID."""
        with self._pool.cursor() as cur:
            cur.execute(
                """
                DELETE FROM holdings
                WHERE id = %s
                """,
                (id,),
            )

    def bulk_create(self, holdings: list[Holding]) -> list[Holding]:
        """Persist multiple holdings in a single operation."""
        if not holdings:
            return []

        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                values = [
                    (
                        h.id,
                        h.session_id,
                        h.ticker,
                        h.name,
                        h.asset_class,
                        h.sector,
                        h.broker,
                        h.purchase_date,
                        h.created_at,
                    )
                    for h in holdings
                ]

                cur.executemany(
                    """
                    INSERT INTO holdings (
                        id, session_id, ticker, name, asset_class,
                        sector, broker, purchase_date, created_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    values,
                )
                conn.commit()

        return holdings

    def _row_to_holding(self, row: tuple) -> Holding:
        """Convert a database row to a Holding model."""
        return Holding(
            id=row[0],
            session_id=row[1],
            ticker=row[2],
            name=row[3],
            asset_class=row[4],
            sector=row[5],
            broker=row[6],
            purchase_date=row[7],
            created_at=row[8],
        )
