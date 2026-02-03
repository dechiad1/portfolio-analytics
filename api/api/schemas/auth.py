from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class UserResponse(BaseModel):
    """Response schema for user info."""

    id: UUID
    email: str
    created_at: datetime
    is_admin: bool = False
