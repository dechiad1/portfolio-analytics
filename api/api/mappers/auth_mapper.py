from domain.models.user import User
from api.schemas.auth import UserResponse


class AuthMapper:
    """Mapper for authentication-related data transformations."""

    @staticmethod
    def to_user_response(user: User) -> UserResponse:
        """Map User to UserResponse."""
        return UserResponse(
            id=user.id,
            email=user.email,
            created_at=user.created_at,
            is_admin=user.is_admin,
        )
