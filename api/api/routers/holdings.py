from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, UploadFile, status

from domain.services.holding_service import (
    HoldingService,
    HoldingNotFoundError,
    HoldingValidationError,
)
from domain.services.session_service import SessionService
from api.schemas.holding import (
    CreateHoldingRequest,
    UpdateHoldingRequest,
    HoldingResponse,
    HoldingListResponse,
    BulkCreateHoldingsResponse,
)
from api.mappers.holding_mapper import HoldingMapper
from dependencies import get_holding_service, get_session_service

router = APIRouter(prefix="/holdings", tags=["holdings"])


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
    response_model=HoldingListResponse,
    summary="List holdings for session",
)
def list_holdings(
    session_id: Annotated[UUID, Depends(validate_session_exists)],
    holding_service: Annotated[HoldingService, Depends(get_holding_service)],
) -> HoldingListResponse:
    """List all holdings for the session."""
    holdings = holding_service.get_holdings_for_session(session_id)
    return HoldingMapper.to_list_response(holdings)


@router.post(
    "",
    response_model=HoldingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a holding",
)
def create_holding(
    request: CreateHoldingRequest,
    session_id: Annotated[UUID, Depends(validate_session_exists)],
    holding_service: Annotated[HoldingService, Depends(get_holding_service)],
) -> HoldingResponse:
    """Create a new holding."""
    try:
        holding = holding_service.create_holding(
            session_id=session_id,
            ticker=request.ticker,
            name=request.name,
            asset_class=request.asset_class,
            sector=request.sector,
            broker=request.broker,
            purchase_date=request.purchase_date,
        )
        return HoldingMapper.to_response(holding)
    except HoldingValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )


@router.post(
    "/upload",
    response_model=BulkCreateHoldingsResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload CSV file to create holdings",
)
async def upload_holdings(
    file: UploadFile,
    session_id: Annotated[UUID, Depends(validate_session_exists)],
    holding_service: Annotated[HoldingService, Depends(get_holding_service)],
) -> BulkCreateHoldingsResponse:
    """Upload a CSV file to bulk create holdings."""
    if file.content_type not in ("text/csv", "application/csv", "text/plain"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="File must be a CSV",
        )

    try:
        content = await file.read()
        csv_content = content.decode("utf-8")
        holdings = holding_service.parse_and_create_holdings_from_csv(
            session_id, csv_content
        )
        return HoldingMapper.to_bulk_create_response(holdings)
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="File must be UTF-8 encoded",
        )
    except HoldingValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )


@router.put(
    "/{holding_id}",
    response_model=HoldingResponse,
    summary="Update a holding",
)
def update_holding(
    holding_id: UUID,
    request: UpdateHoldingRequest,
    session_id: Annotated[UUID, Depends(validate_session_exists)],
    holding_service: Annotated[HoldingService, Depends(get_holding_service)],
) -> HoldingResponse:
    """Update an existing holding."""
    existing = holding_service.get_holding(holding_id)
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Holding {holding_id} not found",
        )

    if existing.session_id != session_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Holding does not belong to this session",
        )

    try:
        updated = holding_service.update_holding(
            holding_id=holding_id,
            ticker=request.ticker,
            name=request.name,
            asset_class=request.asset_class,
            sector=request.sector,
            broker=request.broker,
            purchase_date=request.purchase_date,
        )
        return HoldingMapper.to_response(updated)
    except HoldingNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Holding {holding_id} not found",
        )
    except HoldingValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )


@router.delete(
    "/{holding_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a holding",
)
def delete_holding(
    holding_id: UUID,
    session_id: Annotated[UUID, Depends(validate_session_exists)],
    holding_service: Annotated[HoldingService, Depends(get_holding_service)],
) -> None:
    """Delete a holding."""
    existing = holding_service.get_holding(holding_id)
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Holding {holding_id} not found",
        )

    if existing.session_id != session_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Holding does not belong to this session",
        )

    try:
        holding_service.delete_holding(holding_id)
    except HoldingNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Holding {holding_id} not found",
        )
