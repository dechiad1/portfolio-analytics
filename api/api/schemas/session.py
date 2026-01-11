from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class SessionResponse(BaseModel):
    """Response schema for session details."""

    id: UUID
    created_at: datetime
    last_accessed_at: datetime


class CreateSessionResponse(BaseModel):
    """Response schema for session creation."""

    session_id: UUID
    created_at: datetime
