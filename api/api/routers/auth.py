from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from domain.services.oauth_service import OAuthService, AuthenticationError
from domain.models.user import User
from api.schemas.auth import UserResponse
from api.mappers.auth_mapper import AuthMapper
from dependencies import get_oauth_service

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer(auto_error=False)


def get_current_user_id(
    request: Request,
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
    oauth_service: Annotated[OAuthService, Depends(get_oauth_service)],
) -> UUID:
    """Extract and verify user ID from session cookie."""
    session_token = request.cookies.get("session")
    if session_token is not None:
        try:
            user = oauth_service.verify_session_token(session_token)
            return user.id
        except AuthenticationError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e),
            )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
    )


def get_current_user_full(
    request: Request,
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
    oauth_service: Annotated[OAuthService, Depends(get_oauth_service)],
) -> User:
    """Get the full current user object including is_admin."""
    session_token = request.cookies.get("session")
    if session_token is not None:
        try:
            return oauth_service.verify_session_token(session_token)
        except AuthenticationError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e),
            )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user info",
)
def get_current_user(
    user: Annotated[User, Depends(get_current_user_full)],
) -> UserResponse:
    """Get the current authenticated user's info."""
    return AuthMapper.to_user_response(user)
