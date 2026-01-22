from domain.models.user import User
from api.schemas.auth import AuthResponse, UserResponse


class AuthMapper:
    """Mapper for authentication-related data transformations."""

    @staticmethod
    def to_auth_response(user: User, token: str) -> AuthResponse:
        """Map User and token to AuthResponse."""
        return AuthResponse(
            user_id=user.id,
            email=user.email,
            access_token=token,
        )

    @staticmethod
    def to_user_response(user: User) -> UserResponse:
        """Map User to UserResponse."""
        return UserResponse(
            id=user.id,
            email=user.email,
            created_at=user.created_at,
            is_admin=user.is_admin,
        )
