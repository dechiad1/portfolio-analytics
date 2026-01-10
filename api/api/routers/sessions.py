from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from domain.services.session_service import SessionService
from api.schemas.session import SessionResponse, CreateSessionResponse
from api.mappers.session_mapper import SessionMapper
from dependencies import get_session_service

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post(
    "",
    response_model=CreateSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new session",
)
def create_session(
    session_service: Annotated[SessionService, Depends(get_session_service)],
) -> CreateSessionResponse:
    """Create a new session and return the session ID."""
    session = session_service.create_session()
    return SessionMapper.to_create_response(session)


@router.get(
    "/{session_id}",
    response_model=SessionResponse,
    summary="Get session details",
)
def get_session(
    session_id: UUID,
    session_service: Annotated[SessionService, Depends(get_session_service)],
) -> SessionResponse:
    """Retrieve session details by ID."""
    session = session_service.get_session(session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )

    session_service.touch_session(session_id)
    return SessionMapper.to_response(session)
