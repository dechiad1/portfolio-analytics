from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from domain.services.auth_service import (
    AuthService,
    AuthenticationError,
    UserExistsError,
)
from domain.services.oauth_service import OAuthService, AuthenticationError as OAuthError
from api.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    AuthResponse,
    UserResponse,
)
from api.mappers.auth_mapper import AuthMapper
from dependencies import get_auth_service, get_oauth_service

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer(auto_error=False)


from domain.models.user import User


def get_current_user_id(
    request: Request,
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    oauth_service: Annotated[OAuthService, Depends(get_oauth_service)],
) -> UUID:
    """Extract and verify user ID from JWT token (Bearer) or session cookie."""
    # Try Bearer token first
    if credentials is not None:
        try:
            return auth_service.verify_token(credentials.credentials)
        except AuthenticationError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e),
                headers={"WWW-Authenticate": "Bearer"},
            )

    # Try session cookie
    session_token = request.cookies.get("session")
    if session_token is not None:
        try:
            user = oauth_service.verify_session_token(session_token)
            return user.id
        except OAuthError as e:
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
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    oauth_service: Annotated[OAuthService, Depends(get_oauth_service)],
) -> User:
    """Get the full current user object including is_admin."""
    # Try Bearer token first
    if credentials is not None:
        try:
            user_id = auth_service.verify_token(credentials.credentials)
            user = auth_service.get_user(user_id)
            if user is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found",
                )
            return user
        except AuthenticationError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e),
                headers={"WWW-Authenticate": "Bearer"},
            )

    # Try session cookie
    session_token = request.cookies.get("session")
    if session_token is not None:
        try:
            return oauth_service.verify_session_token(session_token)
        except OAuthError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e),
            )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
    )


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
def register(
    request: RegisterRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> AuthResponse:
    """Register a new user account."""
    try:
        user = auth_service.register(request.email, request.password)
        _, token = auth_service.login(request.email, request.password)
        return AuthMapper.to_auth_response(user, token)
    except UserExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Login to get access token",
)
def login(
    request: LoginRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> AuthResponse:
    """Authenticate and get JWT token."""
    try:
        user, token = auth_service.login(request.email, request.password)
        return AuthMapper.to_auth_response(user, token)
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user info",
)
def get_current_user(
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserResponse:
    """Get the current authenticated user's info."""
    user = auth_service.get_user(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return AuthMapper.to_user_response(user)
