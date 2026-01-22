from decimal import Decimal
from uuid import UUID

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
                    id, portfolio_id, ticker, name, asset_type, asset_class,
                    sector, broker, quantity, purchase_price, current_price,
                    purchase_date, created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, portfolio_id, ticker, name, asset_type, asset_class,
                          sector, broker, quantity, purchase_price, current_price,
                          purchase_date, created_at
                """,
                (
                    holding.id,
                    holding.portfolio_id,
                    holding.ticker,
                    holding.name,
                    holding.asset_type,
                    holding.asset_class,
                    holding.sector,
                    holding.broker,
                    holding.quantity,
                    holding.purchase_price,
                    holding.current_price,
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
                SELECT id, portfolio_id, ticker, name, asset_type, asset_class,
                       sector, broker, quantity, purchase_price, current_price,
                       purchase_date, created_at
                FROM holdings
                WHERE id = %s
                """,
                (id,),
            )
            row = cur.fetchone()

        if row is None:
            return None

        return self._row_to_holding(row)

    def get_by_portfolio_id(self, portfolio_id: UUID) -> list[Holding]:
        """Retrieve all holdings for a portfolio."""
        with self._pool.cursor() as cur:
            cur.execute(
                """
                SELECT id, portfolio_id, ticker, name, asset_type, asset_class,
                       sector, broker, quantity, purchase_price, current_price,
                       purchase_date, created_at
                FROM holdings
                WHERE portfolio_id = %s
                ORDER BY created_at ASC
                """,
                (portfolio_id,),
            )
            rows = cur.fetchall()

        return [self._row_to_holding(row) for row in rows]

    def get_all(self) -> list[Holding]:
        """Retrieve all holdings."""
        with self._pool.cursor() as cur:
            cur.execute(
                """
                SELECT id, portfolio_id, ticker, name, asset_type, asset_class,
                       sector, broker, quantity, purchase_price, current_price,
                       purchase_date, created_at
                FROM holdings
                ORDER BY created_at ASC
                """
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
                    asset_type = %s,
                    asset_class = %s,
                    sector = %s,
                    broker = %s,
                    quantity = %s,
                    purchase_price = %s,
                    current_price = %s,
                    purchase_date = %s
                WHERE id = %s
                RETURNING id, portfolio_id, ticker, name, asset_type, asset_class,
                          sector, broker, quantity, purchase_price, current_price,
                          purchase_date, created_at
                """,
                (
                    holding.ticker,
                    holding.name,
                    holding.asset_type,
                    holding.asset_class,
                    holding.sector,
                    holding.broker,
                    holding.quantity,
                    holding.purchase_price,
                    holding.current_price,
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
                        h.portfolio_id,
                        h.ticker,
                        h.name,
                        h.asset_type,
                        h.asset_class,
                        h.sector,
                        h.broker,
                        h.quantity,
                        h.purchase_price,
                        h.current_price,
                        h.purchase_date,
                        h.created_at,
                    )
                    for h in holdings
                ]

                cur.executemany(
                    """
                    INSERT INTO holdings (
                        id, portfolio_id, ticker, name, asset_type, asset_class,
                        sector, broker, quantity, purchase_price, current_price,
                        purchase_date, created_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    values,
                )
                conn.commit()

        return holdings

    def _row_to_holding(self, row: tuple) -> Holding:
        """Convert a database row to a Holding model."""
        return Holding(
            id=row[0],
            portfolio_id=row[1],
            ticker=row[2],
            name=row[3],
            asset_type=row[4] or "equity",
            asset_class=row[5],
            sector=row[6],
            broker=row[7],
            quantity=Decimal(str(row[8])) if row[8] else Decimal("0"),
            purchase_price=Decimal(str(row[9])) if row[9] else Decimal("0"),
            current_price=Decimal(str(row[10])) if row[10] else None,
            purchase_date=row[11],
            created_at=row[12],
        )
