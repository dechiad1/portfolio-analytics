from abc import ABC, abstractmethod
from uuid import UUID

from domain.models.session import Session


class SessionRepository(ABC):
    """Port for session persistence operations."""

    @abstractmethod
    def create(self, session: Session) -> Session:
        """Persist a new session."""
        pass

    @abstractmethod
    def get_by_id(self, id: UUID) -> Session | None:
        """Retrieve a session by its ID."""
        pass

    @abstractmethod
    def update_last_accessed(self, id: UUID) -> None:
        """Update the last_accessed_at timestamp for a session."""
        pass
