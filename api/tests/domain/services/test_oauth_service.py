from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4

import jwt
import pytest

from domain.models.user import User
from domain.services.oauth_service import AuthenticationError, OAuthService
from domain.value_objects import OAuthTokens, OAuthUserInfo


@pytest.fixture
def user_id():
    return uuid4()


@pytest.fixture
def mock_user(user_id):
    return User(
        id=user_id,
        email="user@example.com",
        password_hash=None,
        created_at=datetime.now(timezone.utc),
        is_admin=False,
        oauth_provider="google",
        oauth_subject="google-sub-123",
    )


@pytest.fixture
def mock_user_repository(mock_user):
    repo = MagicMock()
    repo.get_by_oauth_subject.return_value = mock_user
    repo.get_by_email.return_value = mock_user
    repo.get_by_id.return_value = mock_user
    repo.create.side_effect = lambda u: u
    return repo


@pytest.fixture
def mock_oauth_provider():
    provider = MagicMock()
    provider.get_provider_name.return_value = "google"
    provider.get_authorization_url.return_value = "https://auth.example.com/authorize?state=abc"
    provider.exchange_code_for_tokens.return_value = OAuthTokens(
        access_token="access-tok",
        id_token="id-tok",
    )
    provider.validate_id_token.return_value = OAuthUserInfo(
        subject="google-sub-123",
        email="user@example.com",
        email_verified=True,
        name="Test User",
    )
    return provider


@pytest.fixture
def oauth_service(mock_user_repository, mock_oauth_provider):
    return OAuthService(
        user_repository=mock_user_repository,
        oauth_provider=mock_oauth_provider,
        jwt_secret="test-secret",
    )


class TestGenerateStateAndNonce:
    def test_returns_two_unique_strings(self, oauth_service):
        state, nonce = oauth_service.generate_state_and_nonce()
        assert isinstance(state, str)
        assert isinstance(nonce, str)
        assert state != nonce
        assert len(state) > 20
        assert len(nonce) > 20


class TestGetAuthorizationUrl:
    def test_delegates_to_provider(self, oauth_service, mock_oauth_provider):
        url = oauth_service.get_authorization_url("state", "nonce")
        mock_oauth_provider.get_authorization_url.assert_called_once_with("state", "nonce")
        assert "authorize" in url


class TestHandleCallback:
    def test_returns_user_and_session_token(self, oauth_service, mock_user):
        user, token = oauth_service.handle_callback("auth-code", "expected-nonce")
        assert user.id == mock_user.id
        assert token is not None

    def test_exchanges_code_and_validates(self, oauth_service, mock_oauth_provider):
        oauth_service.handle_callback("auth-code", "nonce")
        mock_oauth_provider.exchange_code_for_tokens.assert_called_once_with("auth-code")
        mock_oauth_provider.validate_id_token.assert_called_once_with("id-tok", "nonce")

    def test_updates_last_login(self, oauth_service, mock_user_repository, mock_user):
        oauth_service.handle_callback("code", "nonce")
        mock_user_repository.update_last_login.assert_called_once()

    def test_creates_new_user_when_not_found(self, oauth_service, mock_user_repository):
        mock_user_repository.get_by_oauth_subject.return_value = None
        mock_user_repository.get_by_email.return_value = None
        user, token = oauth_service.handle_callback("code", "nonce")
        mock_user_repository.create.assert_called_once()
        assert user.email == "user@example.com"
        assert user.oauth_provider == "google"

    def test_finds_existing_user_by_email_when_oauth_subject_missing(
        self, oauth_service, mock_user_repository, mock_user
    ):
        mock_user_repository.get_by_oauth_subject.return_value = None
        user, _ = oauth_service.handle_callback("code", "nonce")
        assert user.id == mock_user.id


class TestAdminPromotion:
    def test_promotes_admin_email_on_oauth_subject_match(
        self, mock_user_repository, mock_oauth_provider
    ):
        admin_user = User(
            id=uuid4(),
            email=OAuthService.ADMIN_EMAIL,
            password_hash=None,
            created_at=datetime.now(timezone.utc),
            is_admin=False,
            oauth_provider="google",
            oauth_subject="admin-sub",
        )
        mock_user_repository.get_by_oauth_subject.return_value = admin_user
        mock_oauth_provider.validate_id_token.return_value = OAuthUserInfo(
            subject="admin-sub",
            email=OAuthService.ADMIN_EMAIL,
        )

        service = OAuthService(
            user_repository=mock_user_repository,
            oauth_provider=mock_oauth_provider,
            jwt_secret="secret",
        )
        user, _ = service.handle_callback("code", "nonce")
        mock_user_repository.set_admin.assert_called_once_with(admin_user.id, True)
        assert user.is_admin is True

    def test_new_admin_email_user_gets_admin(
        self, mock_user_repository, mock_oauth_provider
    ):
        mock_user_repository.get_by_oauth_subject.return_value = None
        mock_user_repository.get_by_email.return_value = None
        mock_oauth_provider.validate_id_token.return_value = OAuthUserInfo(
            subject="new-admin-sub",
            email=OAuthService.ADMIN_EMAIL,
        )
        service = OAuthService(
            user_repository=mock_user_repository,
            oauth_provider=mock_oauth_provider,
            jwt_secret="secret",
        )
        user, _ = service.handle_callback("code", "nonce")
        assert user.is_admin is True


class TestVerifySessionToken:
    def test_returns_user_for_valid_token(self, oauth_service, mock_user):
        _, token = oauth_service.handle_callback("code", "nonce")
        user = oauth_service.verify_session_token(token)
        assert user.id == mock_user.id

    def test_raises_on_expired_token(self, oauth_service):
        payload = {
            "sub": str(uuid4()),
            "email": "x@x.com",
            "is_admin": False,
            "iat": datetime(2020, 1, 1, tzinfo=timezone.utc),
            "exp": datetime(2020, 1, 2, tzinfo=timezone.utc),
        }
        token = jwt.encode(payload, "test-secret", algorithm="HS256")
        with pytest.raises(AuthenticationError, match="expired"):
            oauth_service.verify_session_token(token)

    def test_raises_on_invalid_token(self, oauth_service):
        with pytest.raises(AuthenticationError, match="Invalid session"):
            oauth_service.verify_session_token("garbage")

    def test_raises_when_user_not_found(self, oauth_service, mock_user_repository):
        mock_user_repository.get_by_id.return_value = None
        payload = {
            "sub": str(uuid4()),
            "email": "x@x.com",
            "is_admin": False,
            "iat": datetime.now(timezone.utc),
            "exp": datetime(2099, 1, 1, tzinfo=timezone.utc),
        }
        token = jwt.encode(payload, "test-secret", algorithm="HS256")
        with pytest.raises(AuthenticationError, match="User not found"):
            oauth_service.verify_session_token(token)
