from uuid import UUID

from pydantic import BaseModel


class Security(BaseModel):
    """Represents a security in the registry."""

    security_id: UUID
    ticker: str
    display_name: str
    asset_type: str  # EQUITY, ETF, BOND, CASH
    currency: str
    sector: str | None = None
    industry: str | None = None
    exchange: str | None = None

    model_config = {"frozen": True}
