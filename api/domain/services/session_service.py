from datetime import datetime, timezone
from uuid import UUID, uuid4

from domain.models.session import Session
from domain.ports.session_repository import SessionRepository


class SessionService:
    """Service for managing user sessions."""

    def __init__(self, session_repository: SessionRepository) -> None:
        self._repository = session_repository

    def create_session(self) -> Session:
        """Create a new session with current timestamps."""
        now = datetime.now(timezone.utc)
        session = Session(
            id=uuid4(),
            created_at=now,
            last_accessed_at=now,
        )
        return self._repository.create(session)

    def get_session(self, session_id: UUID) -> Session | None:
        """Retrieve a session by ID."""
        return self._repository.get_by_id(session_id)

    def touch_session(self, session_id: UUID) -> None:
        """Update the last_accessed_at timestamp for a session."""
        self._repository.update_last_accessed(session_id)
