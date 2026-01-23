from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class User(BaseModel):
    """Represents a user account."""

    id: UUID
    email: str
    password_hash: Optional[str] = None
    created_at: datetime
    is_admin: bool = False
    last_login: Optional[datetime] = None
    oauth_provider: Optional[str] = None
    oauth_subject: Optional[str] = None

    model_config = {"frozen": True}
