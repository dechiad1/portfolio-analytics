from abc import ABC, abstractmethod
from uuid import UUID

from domain.models.transaction import Transaction


class TransactionRepository(ABC):
    """Port for transaction persistence operations."""

    @abstractmethod
    def create(self, transaction: Transaction) -> Transaction:
        """Persist a new transaction (append-only)."""
        pass

    @abstractmethod
    def get_by_portfolio_id(self, portfolio_id: UUID) -> list[Transaction]:
        """Retrieve all transactions for a portfolio, ordered by event_ts."""
        pass

    @abstractmethod
    def get_by_portfolio_and_security(
        self, portfolio_id: UUID, security_id: UUID
    ) -> list[Transaction]:
        """Retrieve all transactions for a specific position."""
        pass

    @abstractmethod
    def bulk_create(self, transactions: list[Transaction]) -> list[Transaction]:
        """Persist multiple transactions."""
        pass
