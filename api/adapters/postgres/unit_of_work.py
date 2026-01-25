from contextlib import contextmanager
from typing import Generator

import psycopg

from adapters.postgres.connection import PostgresConnectionPool
from domain.ports.unit_of_work import TransactionContext, UnitOfWork


class PostgresTransactionContext:
    """Postgres implementation of TransactionContext."""

    def __init__(self, cursor: psycopg.Cursor) -> None:
        self._cursor = cursor

    def execute(self, query: str, params: tuple | None = None) -> None:
        """Execute a query within the transaction."""
        self._cursor.execute(query, params)

    def fetchone(self) -> tuple | None:
        """Fetch one result from the last query."""
        return self._cursor.fetchone()

    def fetchall(self) -> list[tuple]:
        """Fetch all results from the last query."""
        return self._cursor.fetchall()


class PostgresUnitOfWork(UnitOfWork):
    """Postgres implementation of UnitOfWork port."""

    def __init__(self, pool: PostgresConnectionPool) -> None:
        self._pool = pool

    @contextmanager
    def transaction(self) -> Generator[TransactionContext, None, None]:
        """
        Start a transaction and yield a context for executing operations.

        On successful completion, the transaction is committed.
        On exception, the transaction is rolled back.
        """
        with self._pool.transaction() as cursor:
            yield PostgresTransactionContext(cursor)
