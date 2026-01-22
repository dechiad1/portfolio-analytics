from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class Portfolio(BaseModel):
    """Represents a user's investment portfolio."""

    id: UUID
    user_id: UUID
    name: str
    base_currency: str = "USD"
    created_at: datetime
    updated_at: datetime

    model_config = {"frozen": True}
