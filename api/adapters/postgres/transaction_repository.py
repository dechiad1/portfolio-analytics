from decimal import Decimal
from uuid import UUID, uuid4

from adapters.postgres.connection import PostgresConnectionPool
from domain.models.transaction import Transaction, TransactionType
from domain.ports.transaction_repository import TransactionRepository


class PostgresTransactionRepository(TransactionRepository):
    """PostgreSQL implementation of TransactionRepository."""

    def __init__(self, pool: PostgresConnectionPool) -> None:
        self._pool = pool

    def create(self, transaction: Transaction) -> Transaction:
        """Persist a new transaction (append-only)."""
        txn_id = transaction.txn_id or uuid4()

        with self._pool.cursor() as cur:
            cur.execute(
                """
                INSERT INTO transaction_ledger (
                    txn_id, portfolio_id, event_ts, txn_type, security_id,
                    quantity, price, fees, currency, notes
                )
                VALUES (%s, %s, %s, %s::transaction_type, %s, %s, %s, %s, %s, %s)
                RETURNING txn_id, portfolio_id, event_ts, txn_type::text, security_id,
                          quantity, price, fees, currency, notes, created_at
                """,
                (
                    txn_id,
                    transaction.portfolio_id,
                    transaction.event_ts,
                    transaction.txn_type.value,
                    transaction.security_id,
                    transaction.quantity,
                    transaction.price,
                    transaction.fees,
                    transaction.currency,
                    transaction.notes,
                ),
            )
            row = cur.fetchone()

        if row is None:
            raise RuntimeError("Failed to create transaction")

        return self._row_to_transaction(row)

    def get_by_portfolio_id(self, portfolio_id: UUID) -> list[Transaction]:
        """Retrieve all transactions for a portfolio, ordered by event_ts."""
        with self._pool.cursor() as cur:
            cur.execute(
                """
                SELECT
                    txn_id, portfolio_id, event_ts, txn_type::text, security_id,
                    quantity, price, fees, currency, notes, created_at
                FROM transaction_ledger
                WHERE portfolio_id = %s
                ORDER BY event_ts ASC
                """,
                (portfolio_id,),
            )
            rows = cur.fetchall()

        return [self._row_to_transaction(row) for row in rows]

    def get_by_portfolio_and_security(
        self, portfolio_id: UUID, security_id: UUID
    ) -> list[Transaction]:
        """Retrieve all transactions for a specific position."""
        with self._pool.cursor() as cur:
            cur.execute(
                """
                SELECT
                    txn_id, portfolio_id, event_ts, txn_type::text, security_id,
                    quantity, price, fees, currency, notes, created_at
                FROM transaction_ledger
                WHERE portfolio_id = %s AND security_id = %s
                ORDER BY event_ts ASC
                """,
                (portfolio_id, security_id),
            )
            rows = cur.fetchall()

        return [self._row_to_transaction(row) for row in rows]

    def bulk_create(self, transactions: list[Transaction]) -> list[Transaction]:
        """Persist multiple transactions."""
        if not transactions:
            return []

        results = []
        for txn in transactions:
            results.append(self.create(txn))
        return results

    def _row_to_transaction(self, row: tuple) -> Transaction:
        """Convert a database row to a Transaction model."""
        return Transaction(
            txn_id=row[0],
            portfolio_id=row[1],
            event_ts=row[2],
            txn_type=TransactionType(row[3]),
            security_id=row[4],
            quantity=Decimal(str(row[5])) if row[5] else Decimal("0"),
            price=Decimal(str(row[6])) if row[6] else None,
            fees=Decimal(str(row[7])) if row[7] else Decimal("0"),
            currency=row[8] or "USD",
            notes=row[9],
            created_at=row[10],
        )
