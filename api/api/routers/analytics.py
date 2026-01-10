from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status

from domain.commands.compute_analytics import ComputeAnalyticsCommand
from domain.services.session_service import SessionService
from api.schemas.analytics import AnalyticsResponse
from api.mappers.holding_mapper import HoldingMapper
from dependencies import get_compute_analytics_command, get_session_service

router = APIRouter(prefix="/analytics", tags=["analytics"])


def get_session_id(
    x_session_id: Annotated[UUID | None, Header()] = None,
    session_id: Annotated[UUID | None, Query()] = None,
) -> UUID:
    """Extract session ID from header or query parameter."""
    resolved_id = x_session_id or session_id
    if resolved_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session ID required via X-Session-ID header or session_id query parameter",
        )
    return resolved_id


def validate_session_exists(
    session_id: Annotated[UUID, Depends(get_session_id)],
    session_service: Annotated[SessionService, Depends(get_session_service)],
) -> UUID:
    """Validate that the session exists."""
    session = session_service.get_session(session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )
    session_service.touch_session(session_id)
    return session_id


@router.get(
    "",
    response_model=AnalyticsResponse,
    summary="Get portfolio analytics",
)
def get_analytics(
    session_id: Annotated[UUID, Depends(validate_session_exists)],
    command: Annotated[ComputeAnalyticsCommand, Depends(get_compute_analytics_command)],
) -> AnalyticsResponse:
    """Compute and return analytics for the session's holdings."""
    analytics = command.execute(session_id)
    return HoldingMapper.analytics_to_response(analytics)
