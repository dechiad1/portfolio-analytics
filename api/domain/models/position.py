from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from domain.models.security import Security


class Position(BaseModel):
    """Represents a position in a portfolio.

    A position is the cached current state of holdings in a security.
    The source of truth is the transaction ledger.
    """

    portfolio_id: UUID
    security_id: UUID
    quantity: Decimal
    avg_cost: Decimal
    updated_at: datetime

    # Enriched fields (not persisted, populated by service layer)
    security: Security | None = None
    current_price: Decimal | None = None

    model_config = {"frozen": True}

    @property
    def cost_basis(self) -> Decimal:
        """Calculate total cost basis."""
        return self.quantity * self.avg_cost

    @property
    def market_value(self) -> Decimal | None:
        """Calculate current market value."""
        if self.current_price is None:
            return None
        return self.quantity * self.current_price

    @property
    def gain_loss(self) -> Decimal | None:
        """Calculate unrealized gain/loss."""
        mv = self.market_value
        if mv is None:
            return None
        return mv - self.cost_basis

    @property
    def gain_loss_pct(self) -> Decimal | None:
        """Calculate unrealized gain/loss percentage."""
        gl = self.gain_loss
        cb = self.cost_basis
        if gl is None or cb == 0:
            return None
        return (gl / cb) * 100

    @property
    def ticker(self) -> str | None:
        """Get ticker from enriched security."""
        return self.security.ticker if self.security else None
