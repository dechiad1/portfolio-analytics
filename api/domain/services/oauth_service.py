from datetime import datetime, timedelta, timezone
from typing import Tuple
from uuid import uuid4
import secrets

import jwt

from domain.models.user import User
from domain.ports.user_repository import UserRepository
from domain.ports.oauth_provider import OAuthProvider
from domain.value_objects import OAuthUserInfo


class AuthenticationError(Exception):
    """Raised when authentication fails."""

    pass


class OAuthService:
    """Service for OAuth authentication flows."""

    ADMIN_EMAIL = "dechiada@gmail.com"

    def __init__(
        self,
        user_repository: UserRepository,
        oauth_provider: OAuthProvider,
        jwt_secret: str,
        jwt_algorithm: str = "HS256",
        token_expiry_hours: int = 24,
    ) -> None:
        self._repository = user_repository
        self._oauth_provider = oauth_provider
        self._jwt_secret = jwt_secret
        self._jwt_algorithm = jwt_algorithm
        self._token_expiry_hours = token_expiry_hours

    def generate_state_and_nonce(self) -> Tuple[str, str]:
        """Generate state and nonce for OAuth flow."""
        state = secrets.token_urlsafe(32)
        nonce = secrets.token_urlsafe(32)
        return state, nonce

    def get_authorization_url(self, state: str, nonce: str) -> str:
        """Get the OAuth authorization URL."""
        return self._oauth_provider.get_authorization_url(state, nonce)

    def handle_callback(
        self, code: str, expected_nonce: str
    ) -> Tuple[User, str]:
        """
        Handle OAuth callback: exchange code, validate token, create/update user.
        Returns (user, session_token).
        """
        tokens = self._oauth_provider.exchange_code_for_tokens(code)

        user_info = self._oauth_provider.validate_id_token(
            tokens.id_token, expected_nonce
        )

        provider_name = self._oauth_provider.get_provider_name()

        user = self._find_or_create_user(user_info, provider_name)

        now = datetime.now(timezone.utc)
        self._repository.update_last_login(user.id, now)

        session_token = self._create_session_token(user)

        return user, session_token

    def _find_or_create_user(
        self, user_info: OAuthUserInfo, provider_name: str
    ) -> User:
        """Find existing user or create new one."""
        is_admin_email = user_info.email.lower() == self.ADMIN_EMAIL.lower()

        user = self._repository.get_by_oauth_subject(
            provider_name, user_info.subject
        )

        if user is not None:
            # Promote to admin if this is the admin email and not already admin
            if is_admin_email and not user.is_admin:
                self._repository.set_admin(user.id, True)
                return User(
                    id=user.id,
                    email=user.email,
                    password_hash=user.password_hash,
                    created_at=user.created_at,
                    is_admin=True,
                    last_login=user.last_login,
                    oauth_provider=user.oauth_provider,
                    oauth_subject=user.oauth_subject,
                )
            return user

        user = self._repository.get_by_email(user_info.email.lower())

        if user is not None:
            # Promote to admin if this is the admin email and not already admin
            if is_admin_email and not user.is_admin:
                self._repository.set_admin(user.id, True)
                return User(
                    id=user.id,
                    email=user.email,
                    password_hash=user.password_hash,
                    created_at=user.created_at,
                    is_admin=True,
                    last_login=user.last_login,
                    oauth_provider=user.oauth_provider,
                    oauth_subject=user.oauth_subject,
                )
            return user

        user = User(
            id=uuid4(),
            email=user_info.email.lower(),
            password_hash=None,
            created_at=datetime.now(timezone.utc),
            is_admin=is_admin_email,
            last_login=datetime.now(timezone.utc),
            oauth_provider=provider_name,
            oauth_subject=user_info.subject,
        )

        return self._repository.create(user)

    def _create_session_token(self, user: User) -> str:
        """Create JWT session token."""
        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(user.id),
            "email": user.email,
            "is_admin": user.is_admin,
            "iat": now,
            "exp": now + timedelta(hours=self._token_expiry_hours),
        }
        return jwt.encode(payload, self._jwt_secret, algorithm=self._jwt_algorithm)

    def verify_session_token(self, token: str) -> User:
        """Verify session token and return user."""
        from uuid import UUID

        try:
            payload = jwt.decode(
                token,
                self._jwt_secret,
                algorithms=[self._jwt_algorithm],
            )
            user_id = UUID(payload["sub"])
            user = self._repository.get_by_id(user_id)
            if user is None:
                raise AuthenticationError("User not found")
            return user
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Session expired")
        except jwt.InvalidTokenError:
            raise AuthenticationError("Invalid session")
