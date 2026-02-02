"""Service for managing transactions."""

from uuid import UUID

from domain.models.transaction import Transaction
from domain.ports.transaction_repository import TransactionRepository


class TransactionService:
    """Service for retrieving transaction history.

    Transactions are append-only and serve as the source of truth
    for all portfolio positions.
    """

    def __init__(self, transaction_repository: TransactionRepository) -> None:
        self._transaction_repo = transaction_repository

    def get_portfolio_transactions(self, portfolio_id: UUID) -> list[Transaction]:
        """Retrieve all transactions for a portfolio, ordered by event timestamp."""
        return self._transaction_repo.get_by_portfolio_id(portfolio_id)

    def get_position_transactions(
        self, portfolio_id: UUID, security_id: UUID
    ) -> list[Transaction]:
        """Retrieve all transactions for a specific position."""
        return self._transaction_repo.get_by_portfolio_and_security(
            portfolio_id, security_id
        )
