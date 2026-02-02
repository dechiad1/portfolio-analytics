from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID

from pydantic import BaseModel


class TransactionType(str, Enum):
    """Types of transactions in the ledger."""

    BUY = "BUY"
    SELL = "SELL"
    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"
    FEE = "FEE"
    DIVIDEND = "DIVIDEND"
    COUPON = "COUPON"


class Transaction(BaseModel):
    """Represents a transaction in the ledger.

    The transaction ledger is append-only and serves as the source of truth
    for all portfolio positions.
    """

    txn_id: UUID
    portfolio_id: UUID
    security_id: UUID | None
    txn_type: TransactionType
    quantity: Decimal
    price: Decimal | None
    fees: Decimal
    currency: str
    event_ts: datetime
    notes: str | None = None
    created_at: datetime | None = None

    model_config = {"frozen": True}

    @property
    def transaction_value(self) -> Decimal | None:
        """Calculate the total value of the transaction."""
        if self.price is None:
            return None
        return self.quantity * self.price + self.fees
