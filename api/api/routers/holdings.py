from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

from domain.services.holding_service import (
    HoldingService,
    HoldingNotFoundError,
    HoldingValidationError,
)
from api.schemas.holding import (
    CreateHoldingRequest,
    UpdateHoldingRequest,
    HoldingResponse,
    HoldingListResponse,
    BulkCreateHoldingsResponse,
)
from api.mappers.holding_mapper import HoldingMapper
from dependencies import get_holding_service

router = APIRouter(prefix="/holdings", tags=["holdings"])


@router.get(
    "",
    response_model=HoldingListResponse,
    summary="List all holdings",
)
def list_holdings(
    holding_service: Annotated[HoldingService, Depends(get_holding_service)],
) -> HoldingListResponse:
    """List all holdings."""
    holdings = holding_service.get_holdings_for_session(None)
    return HoldingMapper.to_list_response(holdings)


@router.post(
    "",
    response_model=HoldingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a holding",
)
def create_holding(
    request: CreateHoldingRequest,
    holding_service: Annotated[HoldingService, Depends(get_holding_service)],
) -> HoldingResponse:
    """Create a new holding."""
    try:
        holding = holding_service.create_holding(
            session_id=None,
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
            None, csv_content
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
    holding_service: Annotated[HoldingService, Depends(get_holding_service)],
) -> HoldingResponse:
    """Update an existing holding."""
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
    holding_service: Annotated[HoldingService, Depends(get_holding_service)],
) -> None:
    """Delete a holding."""
    try:
        holding_service.delete_holding(holding_id)
    except HoldingNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Holding {holding_id} not found",
        )
