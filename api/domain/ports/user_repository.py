from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from domain.models.user import User


class UserRepository(ABC):
    """Port for user persistence operations."""

    @abstractmethod
    def create(self, user: User) -> User:
        """Persist a new user."""
        pass

    @abstractmethod
    def get_by_id(self, id: UUID) -> User | None:
        """Retrieve a user by ID."""
        pass

    @abstractmethod
    def get_by_email(self, email: str) -> User | None:
        """Retrieve a user by email."""
        pass

    @abstractmethod
    def get_by_oauth_subject(self, provider: str, subject: str) -> User | None:
        """Retrieve a user by OAuth provider and subject."""
        pass

    @abstractmethod
    def update_last_login(self, user_id: UUID, last_login: datetime) -> None:
        """Update the user's last login timestamp."""
        pass

    @abstractmethod
    def set_admin(self, user_id: UUID, is_admin: bool) -> None:
        """Update the user's admin status."""
        pass

    @abstractmethod
    def delete(self, id: UUID) -> None:
        """Delete a user by ID."""
        pass
