from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import UUID

from domain.ports.unit_of_work import TransactionContext


@dataclass
class SecurityInput:
    """Input data for creating a security."""

    ticker: str
    display_name: str
    asset_type: str
    sector: str | None


@dataclass
class PositionInput:
    """Input data for creating a position."""

    portfolio_id: UUID
    security_id: UUID
    quantity: Decimal
    avg_cost: Decimal


@dataclass
class TransactionInput:
    """Input data for creating a transaction."""

    txn_id: UUID
    portfolio_id: UUID
    security_id: UUID
    txn_type: str  # BUY, SELL, etc.
    quantity: Decimal
    price: Decimal
    event_ts: date


class PortfolioBuilderRepository(ABC):
    """
    Port for portfolio building operations that require transactional support.

    These methods are designed to work within a UnitOfWork transaction context,
    allowing multiple operations to be executed atomically.
    """

    @abstractmethod
    def create_portfolio_in_transaction(
        self,
        ctx: TransactionContext,
        portfolio_id: UUID,
        user_id: UUID,
        name: str,
        base_currency: str,
    ) -> tuple:
        """
        Create a portfolio within a transaction context.

        Returns the created portfolio row tuple.
        """
        pass

    @abstractmethod
    def find_security_by_ticker(
        self,
        ctx: TransactionContext,
        ticker: str,
    ) -> UUID | None:
        """
        Find a security by ticker within a transaction context.

        Returns the security_id if found, None otherwise.
        """
        pass

    @abstractmethod
    def create_security_in_transaction(
        self,
        ctx: TransactionContext,
        security_id: UUID,
        security: SecurityInput,
    ) -> None:
        """
        Create a new security with equity details and identifier within a transaction.
        """
        pass

    @abstractmethod
    def create_position_in_transaction(
        self,
        ctx: TransactionContext,
        position: PositionInput,
    ) -> None:
        """
        Create a position within a transaction context.
        """
        pass

    @abstractmethod
    def create_transaction_in_transaction(
        self,
        ctx: TransactionContext,
        transaction: TransactionInput,
    ) -> None:
        """
        Create a transaction record within a transaction context.
        """
        pass
