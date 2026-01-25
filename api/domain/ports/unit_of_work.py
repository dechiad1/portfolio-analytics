from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Generator, Protocol


class TransactionContext(Protocol):
    """Protocol for a transaction context that can execute queries."""

    def execute(self, query: str, params: tuple | None = None) -> None:
        """Execute a query within the transaction."""
        ...

    def fetchone(self) -> tuple | None:
        """Fetch one result from the last query."""
        ...

    def fetchall(self) -> list[tuple]:
        """Fetch all results from the last query."""
        ...


class UnitOfWork(ABC):
    """
    Port for managing database transactions.

    Provides a way to execute multiple operations atomically without
    exposing database-specific details to the domain layer.
    """

    @abstractmethod
    @contextmanager
    def transaction(self) -> Generator[TransactionContext, None, None]:
        """
        Start a transaction and yield a context for executing operations.

        On successful completion, the transaction is committed.
        On exception, the transaction is rolled back.

        Usage:
            with unit_of_work.transaction() as ctx:
                ctx.execute("INSERT INTO ...", (value1, value2))
                ctx.execute("INSERT INTO ...", (value3, value4))
        """
        pass
