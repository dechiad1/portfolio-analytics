from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr


class User(BaseModel):
    """Represents a user account."""

    id: UUID
    email: str
    password_hash: str
    created_at: datetime
    is_admin: bool = False

    model_config = {"frozen": True}
