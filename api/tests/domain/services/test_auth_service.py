from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from uuid import uuid4

import jwt
import pytest

from domain.models.user import User
from domain.services.auth_service import AuthService, AuthenticationError, UserExistsError


@pytest.fixture
def user_id():
    return uuid4()


@pytest.fixture
def mock_user(user_id):
    service = AuthService(user_repository=MagicMock(), jwt_secret="secret")
    password_hash = service._hash_password("correct-password")
    return User(
        id=user_id,
        email="test@example.com",
        password_hash=password_hash,
        created_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def mock_user_repository(mock_user):
    repo = MagicMock()
    repo.get_by_email.return_value = mock_user
    repo.get_by_id.return_value = mock_user
    repo.create.side_effect = lambda u: u
    return repo


@pytest.fixture
def auth_service(mock_user_repository):
    return AuthService(
        user_repository=mock_user_repository,
        jwt_secret="test-secret",
        token_expiry_hours=24,
    )


class TestRegister:
    def test_creates_user_with_hashed_password(self, auth_service, mock_user_repository):
        mock_user_repository.get_by_email.return_value = None
        user = auth_service.register("New@Example.com", "password123")
        assert user.email == "new@example.com"
        assert user.password_hash is not None
        assert ":" in user.password_hash

    def test_raises_when_email_exists(self, auth_service):
        with pytest.raises(UserExistsError):
            auth_service.register("test@example.com", "password")

    def test_normalizes_email(self, auth_service, mock_user_repository):
        mock_user_repository.get_by_email.return_value = None
        user = auth_service.register("  TEST@Example.COM  ", "pw")
        assert user.email == "test@example.com"


class TestLogin:
    def test_returns_user_and_token(self, auth_service, mock_user):
        user, token = auth_service.login("test@example.com", "correct-password")
        assert user.id == mock_user.id
        assert token is not None

    def test_raises_on_wrong_password(self, auth_service):
        with pytest.raises(AuthenticationError, match="Invalid email or password"):
            auth_service.login("test@example.com", "wrong-password")

    def test_raises_when_user_not_found(self, auth_service, mock_user_repository):
        mock_user_repository.get_by_email.return_value = None
        with pytest.raises(AuthenticationError, match="Invalid email or password"):
            auth_service.login("nobody@example.com", "password")

    def test_normalizes_email(self, auth_service, mock_user):
        user, _ = auth_service.login("  TEST@Example.COM  ", "correct-password")
        assert user.id == mock_user.id


class TestVerifyToken:
    def test_returns_user_id_from_valid_token(self, auth_service, mock_user):
        _, token = auth_service.login("test@example.com", "correct-password")
        user_id = auth_service.verify_token(token)
        assert user_id == mock_user.id

    def test_raises_on_expired_token(self, auth_service):
        service = AuthService(
            user_repository=MagicMock(),
            jwt_secret="test-secret",
            token_expiry_hours=-1,
        )
        payload = {
            "sub": str(uuid4()),
            "email": "x@x.com",
            "iat": datetime(2020, 1, 1, tzinfo=timezone.utc),
            "exp": datetime(2020, 1, 2, tzinfo=timezone.utc),
        }
        token = jwt.encode(payload, "test-secret", algorithm="HS256")
        with pytest.raises(AuthenticationError, match="expired"):
            auth_service.verify_token(token)

    def test_raises_on_invalid_token(self, auth_service):
        with pytest.raises(AuthenticationError, match="Invalid token"):
            auth_service.verify_token("garbage-token")

    def test_raises_on_wrong_secret(self, auth_service):
        payload = {"sub": str(uuid4()), "email": "x@x.com", "iat": datetime.now(timezone.utc), "exp": datetime(2099, 1, 1, tzinfo=timezone.utc)}
        token = jwt.encode(payload, "wrong-secret", algorithm="HS256")
        with pytest.raises(AuthenticationError, match="Invalid token"):
            auth_service.verify_token(token)


class TestGetUser:
    def test_returns_user(self, auth_service, mock_user):
        result = auth_service.get_user(mock_user.id)
        assert result.id == mock_user.id

    def test_returns_none_when_not_found(self, auth_service, mock_user_repository):
        mock_user_repository.get_by_id.return_value = None
        assert auth_service.get_user(uuid4()) is None


class TestPasswordHashing:
    def test_hash_produces_salt_and_hash(self, auth_service):
        result = auth_service._hash_password("test")
        salt, hash_hex = result.split(":")
        assert len(salt) == 32  # 16 bytes hex
        assert len(hash_hex) == 64  # sha256 hex

    def test_different_salts_per_call(self, auth_service):
        h1 = auth_service._hash_password("same")
        h2 = auth_service._hash_password("same")
        assert h1 != h2

    def test_verify_correct_password(self, auth_service):
        hashed = auth_service._hash_password("mypassword")
        assert auth_service._verify_password("mypassword", hashed) is True

    def test_verify_wrong_password(self, auth_service):
        hashed = auth_service._hash_password("mypassword")
        assert auth_service._verify_password("wrongpassword", hashed) is False

    def test_verify_malformed_hash(self, auth_service):
        assert auth_service._verify_password("pw", "no-colon-here") is False
        assert auth_service._verify_password("pw", "") is False
