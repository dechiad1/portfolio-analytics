from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class Holding(BaseModel):
    """Represents a portfolio holding."""

    id: UUID
    portfolio_id: UUID | None = None
    ticker: str
    name: str
    asset_type: str = "equity"  # equity, bond, etf, mutual_fund
    asset_class: str
    sector: str
    broker: str
    quantity: Decimal = Decimal("0")
    purchase_price: Decimal = Decimal("0")
    current_price: Decimal | None = None
    purchase_date: date
    created_at: datetime

    model_config = {"frozen": True}

    @property
    def market_value(self) -> Decimal:
        """Calculate current market value."""
        price = self.current_price if self.current_price else self.purchase_price
        return self.quantity * price

    @property
    def cost_basis(self) -> Decimal:
        """Calculate total cost basis."""
        return self.quantity * self.purchase_price

    @property
    def gain_loss(self) -> Decimal:
        """Calculate unrealized gain/loss."""
        return self.market_value - self.cost_basis
