from abc import ABC, abstractmethod
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
    def delete(self, id: UUID) -> None:
        """Delete a user by ID."""
        pass
