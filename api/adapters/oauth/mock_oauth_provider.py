from typing import Optional
from urllib.parse import urlencode

import httpx
import jwt
from jwt import PyJWKClient

from domain.ports.oauth_provider import OAuthProvider, OAuthTokens, OAuthUserInfo


class MockOAuth2Provider(OAuthProvider):
    """Adapter for mock-oauth2-server."""

    def __init__(
        self,
        issuer_url: str,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
    ) -> None:
        self._issuer_url = issuer_url.rstrip("/")
        self._client_id = client_id
        self._client_secret = client_secret
        self._redirect_uri = redirect_uri
        self._jwks_client: Optional[PyJWKClient] = None

    def get_provider_name(self) -> str:
        """Get the provider name."""
        return "mock-oauth2"

    def get_authorization_url(self, state: str, nonce: str) -> str:
        """Generate authorization URL."""
        params = {
            "response_type": "code",
            "client_id": self._client_id,
            "redirect_uri": self._redirect_uri,
            "scope": "openid email profile",
            "state": state,
            "nonce": nonce,
        }
        return f"{self._issuer_url}/authorize?{urlencode(params)}"

    def exchange_code_for_tokens(self, code: str) -> OAuthTokens:
        """Exchange authorization code for tokens."""
        token_url = f"{self._issuer_url}/token"

        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self._redirect_uri,
            "client_id": self._client_id,
            "client_secret": self._client_secret,
        }

        with httpx.Client() as client:
            response = client.post(token_url, data=data)
            response.raise_for_status()
            result = response.json()

        return OAuthTokens(
            access_token=result["access_token"],
            id_token=result["id_token"],
            refresh_token=result.get("refresh_token"),
            expires_in=result.get("expires_in", 3600),
        )

    def validate_id_token(self, id_token: str, nonce: str) -> OAuthUserInfo:
        """Validate ID token using JWKS."""
        if self._jwks_client is None:
            jwks_uri = f"{self._issuer_url}/jwks"
            self._jwks_client = PyJWKClient(jwks_uri)

        signing_key = self._jwks_client.get_signing_key_from_jwt(id_token)

        payload = jwt.decode(
            id_token,
            signing_key.key,
            algorithms=["RS256"],
            audience=self._client_id,
            issuer=self._issuer_url,
        )

        # mock-oauth2-server in interactive mode doesn't preserve nonce in ID token
        # For production OAuth providers, this check should be enforced
        token_nonce = payload.get("nonce")
        if token_nonce is not None and token_nonce != nonce:
            raise ValueError("Invalid nonce in ID token")

        return OAuthUserInfo(
            subject=payload["sub"],
            email=payload["email"],
            email_verified=payload.get("email_verified", False),
            name=payload.get("name"),
        )
