from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel


class Holding(BaseModel):
    """Represents a portfolio holding."""

    id: UUID
    session_id: UUID
    ticker: str
    name: str
    asset_class: str
    sector: str
    broker: str
    purchase_date: date
    created_at: datetime

    model_config = {"frozen": True}
