from abc import ABC, abstractmethod

from domain.value_objects import OAuthTokens, OAuthUserInfo


class OAuthProvider(ABC):
    """Port for OAuth provider operations."""

    @abstractmethod
    def get_authorization_url(self, state: str, nonce: str) -> str:
        """Generate authorization URL for redirect."""
        pass

    @abstractmethod
    def exchange_code_for_tokens(self, code: str) -> OAuthTokens:
        """Exchange authorization code for tokens."""
        pass

    @abstractmethod
    def validate_id_token(self, id_token: str, nonce: str) -> OAuthUserInfo:
        """Validate ID token and extract user info."""
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Get the provider name (e.g., 'mock-oauth2', 'google')."""
        pass
