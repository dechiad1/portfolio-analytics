from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class Session(BaseModel):
    """Represents a user session for portfolio management."""

    id: UUID
    created_at: datetime
    last_accessed_at: datetime

    model_config = {"frozen": True}
