import hashlib
import hmac
import os
import secrets
from datetime import datetime, timezone, timedelta
from uuid import UUID, uuid4

import jwt

from domain.models.user import User
from domain.ports.user_repository import UserRepository


class AuthenticationError(Exception):
    """Raised when authentication fails."""
    pass


class UserExistsError(Exception):
    """Raised when trying to register an existing user."""
    pass


class AuthService:
    """Service for user authentication and authorization."""

    def __init__(
        self,
        user_repository: UserRepository,
        jwt_secret: str,
        jwt_algorithm: str = "HS256",
        token_expiry_hours: int = 24,
    ) -> None:
        self._repository = user_repository
        self._jwt_secret = jwt_secret
        self._jwt_algorithm = jwt_algorithm
        self._token_expiry_hours = token_expiry_hours

    def register(self, email: str, password: str) -> User:
        """Register a new user."""
        email = email.lower().strip()

        existing = self._repository.get_by_email(email)
        if existing is not None:
            raise UserExistsError(f"User with email {email} already exists")

        password_hash = self._hash_password(password)

        user = User(
            id=uuid4(),
            email=email,
            password_hash=password_hash,
            created_at=datetime.now(timezone.utc),
        )
        return self._repository.create(user)

    def login(self, email: str, password: str) -> tuple[User, str]:
        """Authenticate user and return user with JWT token."""
        email = email.lower().strip()

        user = self._repository.get_by_email(email)
        if user is None:
            raise AuthenticationError("Invalid email or password")

        if not self._verify_password(password, user.password_hash):
            raise AuthenticationError("Invalid email or password")

        token = self._create_token(user)
        return user, token

    def verify_token(self, token: str) -> UUID:
        """Verify JWT token and return user ID."""
        try:
            payload = jwt.decode(
                token,
                self._jwt_secret,
                algorithms=[self._jwt_algorithm],
            )
            return UUID(payload["sub"])
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired")
        except jwt.InvalidTokenError:
            raise AuthenticationError("Invalid token")

    def get_user(self, user_id: UUID) -> User | None:
        """Get user by ID."""
        return self._repository.get_by_id(user_id)

    def _hash_password(self, password: str) -> str:
        """Hash password using PBKDF2."""
        salt = secrets.token_hex(16)
        hash_bytes = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            100000,
        )
        return f"{salt}:{hash_bytes.hex()}"

    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash."""
        try:
            salt, stored_hash = password_hash.split(":")
            hash_bytes = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode("utf-8"),
                salt.encode("utf-8"),
                100000,
            )
            return hmac.compare_digest(hash_bytes.hex(), stored_hash)
        except (ValueError, AttributeError):
            return False

    def _create_token(self, user: User) -> str:
        """Create JWT token for user."""
        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(user.id),
            "email": user.email,
            "iat": now,
            "exp": now + timedelta(hours=self._token_expiry_hours),
        }
        return jwt.encode(payload, self._jwt_secret, algorithm=self._jwt_algorithm)
