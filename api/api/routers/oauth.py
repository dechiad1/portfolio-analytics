import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Cookie, Request, Response
from fastapi.responses import RedirectResponse

from domain.services.oauth_service import OAuthService, AuthenticationError

logger = logging.getLogger(__name__)
from domain.models.user import User
from api.schemas.auth import UserResponse
from api.mappers.auth_mapper import AuthMapper
from dependencies import get_oauth_service, load_config

router = APIRouter(prefix="/oauth", tags=["oauth"])

COOKIE_NAME = "session"
COOKIE_MAX_AGE = 24 * 60 * 60


@router.get("/login", summary="Initiate OAuth login")
def oauth_login(
    oauth_service: Annotated[OAuthService, Depends(get_oauth_service)],
) -> RedirectResponse:
    """Redirect to OAuth provider for authentication."""
    state, nonce = oauth_service.generate_state_and_nonce()

    authorization_url = oauth_service.get_authorization_url(state, nonce)

    response = RedirectResponse(
        url=authorization_url,
        status_code=status.HTTP_302_FOUND,
    )

    config = load_config()
    is_secure = any(
        origin.startswith("https") for origin in config.server.cors_origins
    )

    response.set_cookie(
        key="oauth_state",
        value=state,
        httponly=True,
        secure=is_secure,
        samesite="lax",
        max_age=600,
    )
    response.set_cookie(
        key="oauth_nonce",
        value=nonce,
        httponly=True,
        secure=is_secure,
        samesite="lax",
        max_age=600,
    )

    return response


@router.get("/callback", summary="OAuth callback handler")
def oauth_callback(
    code: str,
    state: str,
    oauth_service: Annotated[OAuthService, Depends(get_oauth_service)],
    oauth_state: Annotated[str | None, Cookie()] = None,
    oauth_nonce: Annotated[str | None, Cookie()] = None,
) -> RedirectResponse:
    """Handle OAuth callback from provider."""
    if oauth_state is None or oauth_state != state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state parameter",
        )

    if oauth_nonce is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing nonce",
        )

    try:
        user, session_token = oauth_service.handle_callback(
            code=code,
            expected_nonce=oauth_nonce,
        )
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
    except Exception as e:
        logger.exception("OAuth callback failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed",
        )

    config = load_config()
    frontend_url = config.server.frontend_url
    is_secure = frontend_url.startswith("https")

    response = RedirectResponse(
        url=f"{frontend_url}/portfolios",
        status_code=status.HTTP_302_FOUND,
    )

    response.set_cookie(
        key=COOKIE_NAME,
        value=session_token,
        httponly=True,
        secure=is_secure,
        samesite="lax",
        max_age=COOKIE_MAX_AGE,
    )

    response.delete_cookie("oauth_state")
    response.delete_cookie("oauth_nonce")

    return response


@router.post("/logout", summary="Logout user", status_code=status.HTTP_204_NO_CONTENT)
def oauth_logout() -> Response:
    """Clear session cookie to log out user."""
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    response.delete_cookie(COOKIE_NAME)
    return response


def get_current_user_from_cookie(
    request: Request,
    oauth_service: Annotated[OAuthService, Depends(get_oauth_service)],
) -> User:
    """Extract and verify user from session cookie."""
    session_token = request.cookies.get(COOKIE_NAME)

    if session_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    try:
        return oauth_service.verify_session_token(session_token)
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


@router.get("/me", response_model=UserResponse, summary="Get current user")
def get_current_user(
    request: Request,
    oauth_service: Annotated[OAuthService, Depends(get_oauth_service)],
) -> UserResponse:
    """Get the current authenticated user's info."""
    user = get_current_user_from_cookie(request, oauth_service)
    return AuthMapper.to_user_response(user)
