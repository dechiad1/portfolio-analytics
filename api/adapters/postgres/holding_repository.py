from decimal import Decimal
from uuid import UUID, uuid4
from datetime import datetime, timezone

from domain.models.holding import Holding
from domain.ports.holding_repository import HoldingRepository

from adapters.postgres.connection import PostgresConnectionPool


class PostgresHoldingRepository(HoldingRepository):
    """PostgreSQL implementation of HoldingRepository using v1 schema."""

    def __init__(self, pool: PostgresConnectionPool) -> None:
        self._pool = pool

    def create(self, holding: Holding) -> Holding:
        """Persist a new holding (creates security + position)."""
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                # First, check if security already exists by ticker
                cur.execute(
                    """
                    SELECT sr.security_id
                    FROM security_registry sr
                    JOIN equity_details ed ON sr.security_id = ed.security_id
                    WHERE ed.ticker = %s
                    """,
                    (holding.ticker,),
                )
                row = cur.fetchone()

                if row:
                    security_id = row[0]
                else:
                    # Create new security
                    security_id = uuid4()
                    asset_type = holding.asset_type.upper()
                    if asset_type not in ('EQUITY', 'ETF', 'BOND', 'CASH'):
                        asset_type = 'EQUITY'

                    cur.execute(
                        """
                        INSERT INTO security_registry (security_id, asset_type, currency, display_name, is_active)
                        VALUES (%s, %s::asset_type, 'USD', %s, true)
                        """,
                        (security_id, asset_type, holding.name),
                    )

                    cur.execute(
                        """
                        INSERT INTO equity_details (security_id, ticker, sector)
                        VALUES (%s, %s, %s)
                        """,
                        (security_id, holding.ticker, holding.sector),
                    )

                    cur.execute(
                        """
                        INSERT INTO security_identifier (security_id, id_type, id_value, is_primary)
                        VALUES (%s, 'TICKER'::identifier_type, %s, true)
                        """,
                        (security_id, holding.ticker),
                    )

                # Create position
                cur.execute(
                    """
                    INSERT INTO position_current (
                        portfolio_id, security_id, quantity, avg_cost,
                        broker, purchase_date, current_price, asset_class
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING portfolio_id, security_id, quantity, avg_cost,
                              broker, purchase_date, current_price, asset_class, updated_at
                    """,
                    (
                        holding.portfolio_id,
                        security_id,
                        holding.quantity,
                        holding.purchase_price,
                        holding.broker,
                        holding.purchase_date,
                        holding.current_price,
                        holding.asset_class,
                    ),
                )
                pos_row = cur.fetchone()
                conn.commit()

        # Construct the holding from the created data
        return Holding(
            id=security_id,  # Use security_id as the holding ID
            portfolio_id=holding.portfolio_id,
            ticker=holding.ticker,
            name=holding.name,
            asset_type=holding.asset_type,
            asset_class=holding.asset_class,
            sector=holding.sector,
            broker=holding.broker,
            quantity=holding.quantity,
            purchase_price=holding.purchase_price,
            current_price=holding.current_price,
            purchase_date=holding.purchase_date,
            created_at=pos_row[8] if pos_row else datetime.now(timezone.utc),
        )

    def get_by_id(self, id: UUID) -> Holding | None:
        """Retrieve a holding by its security ID."""
        with self._pool.cursor() as cur:
            cur.execute(
                """
                SELECT
                    pc.security_id as id,
                    pc.portfolio_id,
                    ed.ticker,
                    sr.display_name as name,
                    LOWER(sr.asset_type::text) as asset_type,
                    pc.asset_class,
                    COALESCE(ed.sector, 'Unknown') as sector,
                    pc.broker,
                    pc.quantity,
                    pc.avg_cost as purchase_price,
                    pc.current_price,
                    pc.purchase_date,
                    pc.updated_at as created_at
                FROM position_current pc
                JOIN security_registry sr ON pc.security_id = sr.security_id
                LEFT JOIN equity_details ed ON sr.security_id = ed.security_id
                WHERE pc.security_id = %s
                LIMIT 1
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
                SELECT
                    pc.security_id as id,
                    pc.portfolio_id,
                    COALESCE(ed.ticker, 'UNKNOWN') as ticker,
                    sr.display_name as name,
                    LOWER(sr.asset_type::text) as asset_type,
                    pc.asset_class,
                    COALESCE(ed.sector, 'Unknown') as sector,
                    pc.broker,
                    pc.quantity,
                    pc.avg_cost as purchase_price,
                    pc.current_price,
                    pc.purchase_date,
                    pc.updated_at as created_at
                FROM position_current pc
                JOIN security_registry sr ON pc.security_id = sr.security_id
                LEFT JOIN equity_details ed ON sr.security_id = ed.security_id
                WHERE pc.portfolio_id = %s
                ORDER BY pc.updated_at ASC
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
                SELECT
                    pc.security_id as id,
                    pc.portfolio_id,
                    COALESCE(ed.ticker, 'UNKNOWN') as ticker,
                    sr.display_name as name,
                    LOWER(sr.asset_type::text) as asset_type,
                    pc.asset_class,
                    COALESCE(ed.sector, 'Unknown') as sector,
                    pc.broker,
                    pc.quantity,
                    pc.avg_cost as purchase_price,
                    pc.current_price,
                    pc.purchase_date,
                    pc.updated_at as created_at
                FROM position_current pc
                JOIN security_registry sr ON pc.security_id = sr.security_id
                LEFT JOIN equity_details ed ON sr.security_id = ed.security_id
                ORDER BY pc.updated_at ASC
                """
            )
            rows = cur.fetchall()

        return [self._row_to_holding(row) for row in rows]

    def update(self, holding: Holding) -> Holding:
        """Update an existing holding."""
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                # Update security_registry
                asset_type = holding.asset_type.upper()
                if asset_type not in ('EQUITY', 'ETF', 'BOND', 'CASH'):
                    asset_type = 'EQUITY'

                cur.execute(
                    """
                    UPDATE security_registry
                    SET display_name = %s,
                        asset_type = %s::asset_type
                    WHERE security_id = %s
                    """,
                    (holding.name, asset_type, holding.id),
                )

                # Update equity_details
                cur.execute(
                    """
                    UPDATE equity_details
                    SET ticker = %s,
                        sector = %s
                    WHERE security_id = %s
                    """,
                    (holding.ticker, holding.sector, holding.id),
                )

                # Update position_current
                cur.execute(
                    """
                    UPDATE position_current
                    SET quantity = %s,
                        avg_cost = %s,
                        broker = %s,
                        purchase_date = %s,
                        current_price = %s,
                        asset_class = %s
                    WHERE security_id = %s AND portfolio_id = %s
                    RETURNING portfolio_id, security_id, quantity, avg_cost,
                              broker, purchase_date, current_price, asset_class, updated_at
                    """,
                    (
                        holding.quantity,
                        holding.purchase_price,
                        holding.broker,
                        holding.purchase_date,
                        holding.current_price,
                        holding.asset_class,
                        holding.id,
                        holding.portfolio_id,
                    ),
                )
                row = cur.fetchone()
                conn.commit()

        if row is None:
            raise RuntimeError(f"Failed to update holding {holding.id}")

        return Holding(
            id=holding.id,
            portfolio_id=holding.portfolio_id,
            ticker=holding.ticker,
            name=holding.name,
            asset_type=holding.asset_type,
            asset_class=holding.asset_class,
            sector=holding.sector,
            broker=holding.broker,
            quantity=Decimal(str(row[2])) if row[2] else Decimal("0"),
            purchase_price=Decimal(str(row[3])) if row[3] else Decimal("0"),
            current_price=Decimal(str(row[6])) if row[6] else None,
            purchase_date=row[5],
            created_at=row[8],
        )

    def delete(self, id: UUID) -> None:
        """Delete a holding by its security ID."""
        with self._pool.cursor() as cur:
            # Delete position (security can be shared across portfolios)
            cur.execute(
                """
                DELETE FROM position_current
                WHERE security_id = %s
                """,
                (id,),
            )

    def bulk_create(self, holdings: list[Holding]) -> list[Holding]:
        """Persist multiple holdings in a single operation."""
        if not holdings:
            return []

        created = []
        for holding in holdings:
            created.append(self.create(holding))
        return created

    def _row_to_holding(self, row: tuple) -> Holding:
        """Convert a database row to a Holding model."""
        return Holding(
            id=row[0],
            portfolio_id=row[1],
            ticker=row[2] or "UNKNOWN",
            name=row[3],
            asset_type=row[4] or "equity",
            asset_class=row[5] or "Unknown",
            sector=row[6] or "Unknown",
            broker=row[7] or "Unknown",
            quantity=Decimal(str(row[8])) if row[8] else Decimal("0"),
            purchase_price=Decimal(str(row[9])) if row[9] else Decimal("0"),
            current_price=Decimal(str(row[10])) if row[10] else None,
            purchase_date=row[11],
            created_at=row[12],
        )
