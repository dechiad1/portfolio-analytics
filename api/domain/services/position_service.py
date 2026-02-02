"""Service for managing portfolio positions."""

from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from domain.models.position import Position
from domain.models.transaction import Transaction, TransactionType
from domain.ports.position_repository import PositionRepository
from domain.ports.transaction_repository import TransactionRepository


class PositionNotFoundError(Exception):
    """Raised when a position is not found."""

    pass


class SecurityNotFoundError(Exception):
    """Raised when a security is not found."""

    pass


class PositionService:
    """Service for managing portfolio positions.

    Positions are the cached current state of holdings. The source of truth
    is the transaction ledger. All position changes create corresponding
    transactions.
    """

    def __init__(
        self,
        position_repository: PositionRepository,
        transaction_repository: TransactionRepository,
    ) -> None:
        self._position_repo = position_repository
        self._transaction_repo = transaction_repository

    def get_portfolio_positions(self, portfolio_id: UUID) -> list[Position]:
        """Retrieve all positions for a portfolio with enriched security data."""
        return self._position_repo.get_by_portfolio_id(portfolio_id)

    def get_position(
        self, portfolio_id: UUID, security_id: UUID
    ) -> Position | None:
        """Retrieve a single position with enriched security data."""
        return self._position_repo.get_by_portfolio_and_security(
            portfolio_id, security_id
        )

    def add_position(
        self,
        portfolio_id: UUID,
        security_id: UUID,
        quantity: Decimal,
        price: Decimal,
        event_date: date,
    ) -> Position:
        """Add or increase a position by creating a BUY transaction.

        If a position already exists for this security, updates the quantity
        and recalculates the average cost.

        Args:
            portfolio_id: Portfolio to add position to
            security_id: Security to add
            quantity: Number of shares/units to buy
            price: Price per share/unit
            event_date: Date of the transaction

        Returns:
            The created or updated position
        """
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        if price < 0:
            raise ValueError("Price cannot be negative")

        # Create the BUY transaction
        event_ts = datetime.combine(event_date, datetime.min.time(), timezone.utc)
        transaction = Transaction(
            txn_id=uuid4(),
            portfolio_id=portfolio_id,
            security_id=security_id,
            txn_type=TransactionType.BUY,
            quantity=quantity,
            price=price,
            fees=Decimal("0"),
            currency="USD",
            event_ts=event_ts,
            notes=None,
        )
        self._transaction_repo.create(transaction)

        # Get existing position or create new
        existing = self._position_repo.get_by_portfolio_and_security(
            portfolio_id, security_id
        )

        if existing:
            # Calculate new average cost
            old_value = existing.quantity * existing.avg_cost
            new_value = quantity * price
            new_quantity = existing.quantity + quantity
            new_avg_cost = (old_value + new_value) / new_quantity

            updated_position = Position(
                portfolio_id=portfolio_id,
                security_id=security_id,
                quantity=new_quantity,
                avg_cost=new_avg_cost,
                updated_at=datetime.now(timezone.utc),
            )
        else:
            updated_position = Position(
                portfolio_id=portfolio_id,
                security_id=security_id,
                quantity=quantity,
                avg_cost=price,
                updated_at=datetime.now(timezone.utc),
            )

        return self._position_repo.upsert(updated_position)

    def remove_position(
        self, portfolio_id: UUID, security_id: UUID
    ) -> None:
        """Remove a position by creating a SELL transaction for the full quantity.

        Args:
            portfolio_id: Portfolio containing the position
            security_id: Security to remove

        Raises:
            PositionNotFoundError: If position doesn't exist
        """
        existing = self._position_repo.get_by_portfolio_and_security(
            portfolio_id, security_id
        )
        if existing is None:
            raise PositionNotFoundError(
                f"Position for security {security_id} not found in portfolio {portfolio_id}"
            )

        # Create SELL transaction for full quantity
        transaction = Transaction(
            txn_id=uuid4(),
            portfolio_id=portfolio_id,
            security_id=security_id,
            txn_type=TransactionType.SELL,
            quantity=existing.quantity,
            price=existing.avg_cost,  # Use avg cost as sell price
            fees=Decimal("0"),
            currency="USD",
            event_ts=datetime.now(timezone.utc),
            notes="Position removed",
        )
        self._transaction_repo.create(transaction)

        # Delete the position
        self._position_repo.delete(portfolio_id, security_id)

    def bulk_add_positions(
        self,
        portfolio_id: UUID,
        positions_data: list[dict],
    ) -> list[Position]:
        """Add multiple positions in bulk.

        Each item in positions_data should have:
            - security_id: UUID
            - quantity: Decimal
            - price: Decimal
            - event_date: date

        Returns:
            List of created positions
        """
        results = []
        for data in positions_data:
            position = self.add_position(
                portfolio_id=portfolio_id,
                security_id=data["security_id"],
                quantity=data["quantity"],
                price=data["price"],
                event_date=data["event_date"],
            )
            results.append(position)
        return results
