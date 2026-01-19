from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

from domain.services.portfolio_service import (
    PortfolioService,
    PortfolioNotFoundError,
    PortfolioAccessDeniedError,
)
from domain.services.holding_service import (
    HoldingService,
    HoldingNotFoundError,
    HoldingValidationError,
)
from api.schemas.portfolio import (
    CreatePortfolioRequest,
    UpdatePortfolioRequest,
    PortfolioResponse,
    PortfolioListResponse,
    PortfolioSummaryResponse,
)
from api.schemas.holding import (
    CreateHoldingRequest,
    UpdateHoldingRequest,
    HoldingResponse,
    HoldingListResponse,
    BulkCreateHoldingsResponse,
)
from api.schemas.risk_analysis import RiskAnalysisResponse, RiskItem
from api.mappers.portfolio_mapper import PortfolioMapper
from api.mappers.holding_mapper import HoldingMapper
from api.routers.auth import get_current_user_id
from domain.services.risk_analysis_service import RiskAnalysisService
from dependencies import get_portfolio_service, get_holding_service, get_risk_analysis_service

router = APIRouter(prefix="/portfolios", tags=["portfolios"])


@router.get(
    "",
    response_model=PortfolioListResponse,
    summary="List user's portfolios",
)
def list_portfolios(
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    portfolio_service: Annotated[PortfolioService, Depends(get_portfolio_service)],
) -> PortfolioListResponse:
    """List all portfolios for the authenticated user."""
    portfolios = portfolio_service.get_user_portfolios(user_id)
    return PortfolioMapper.to_list_response(portfolios)


@router.post(
    "",
    response_model=PortfolioResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a portfolio",
)
def create_portfolio(
    request: CreatePortfolioRequest,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    portfolio_service: Annotated[PortfolioService, Depends(get_portfolio_service)],
) -> PortfolioResponse:
    """Create a new portfolio."""
    portfolio = portfolio_service.create_portfolio(
        user_id=user_id,
        name=request.name,
        description=request.description,
    )
    return PortfolioMapper.to_response(portfolio)


@router.get(
    "/{portfolio_id}",
    response_model=PortfolioResponse,
    summary="Get a portfolio",
)
def get_portfolio(
    portfolio_id: UUID,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    portfolio_service: Annotated[PortfolioService, Depends(get_portfolio_service)],
) -> PortfolioResponse:
    """Get a portfolio by ID."""
    try:
        portfolio = portfolio_service.get_portfolio(portfolio_id, user_id)
        return PortfolioMapper.to_response(portfolio)
    except PortfolioNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio {portfolio_id} not found",
        )
    except PortfolioAccessDeniedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this portfolio",
        )


@router.put(
    "/{portfolio_id}",
    response_model=PortfolioResponse,
    summary="Update a portfolio",
)
def update_portfolio(
    portfolio_id: UUID,
    request: UpdatePortfolioRequest,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    portfolio_service: Annotated[PortfolioService, Depends(get_portfolio_service)],
) -> PortfolioResponse:
    """Update a portfolio."""
    try:
        portfolio = portfolio_service.update_portfolio(
            portfolio_id=portfolio_id,
            user_id=user_id,
            name=request.name,
            description=request.description,
        )
        return PortfolioMapper.to_response(portfolio)
    except PortfolioNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio {portfolio_id} not found",
        )
    except PortfolioAccessDeniedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this portfolio",
        )


@router.delete(
    "/{portfolio_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a portfolio",
)
def delete_portfolio(
    portfolio_id: UUID,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    portfolio_service: Annotated[PortfolioService, Depends(get_portfolio_service)],
) -> None:
    """Delete a portfolio and all its holdings."""
    try:
        portfolio_service.delete_portfolio(portfolio_id, user_id)
    except PortfolioNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio {portfolio_id} not found",
        )
    except PortfolioAccessDeniedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this portfolio",
        )


@router.get(
    "/{portfolio_id}/summary",
    response_model=PortfolioSummaryResponse,
    summary="Get portfolio summary with breakdowns",
)
def get_portfolio_summary(
    portfolio_id: UUID,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    portfolio_service: Annotated[PortfolioService, Depends(get_portfolio_service)],
) -> PortfolioSummaryResponse:
    """Get portfolio summary with asset type, class, and sector breakdowns."""
    try:
        summary = portfolio_service.get_portfolio_summary(portfolio_id, user_id)
        return PortfolioMapper.to_summary_response(summary)
    except PortfolioNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio {portfolio_id} not found",
        )
    except PortfolioAccessDeniedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this portfolio",
        )


# Holdings within a portfolio
@router.get(
    "/{portfolio_id}/holdings",
    response_model=HoldingListResponse,
    summary="List portfolio holdings",
)
def list_holdings(
    portfolio_id: UUID,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    portfolio_service: Annotated[PortfolioService, Depends(get_portfolio_service)],
) -> HoldingListResponse:
    """List all holdings in a portfolio."""
    try:
        holdings = portfolio_service.get_portfolio_holdings(portfolio_id, user_id)
        return HoldingMapper.to_list_response(holdings)
    except PortfolioNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio {portfolio_id} not found",
        )
    except PortfolioAccessDeniedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this portfolio",
        )


@router.post(
    "/{portfolio_id}/holdings",
    response_model=HoldingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add holding to portfolio",
)
def create_holding(
    portfolio_id: UUID,
    request: CreateHoldingRequest,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    portfolio_service: Annotated[PortfolioService, Depends(get_portfolio_service)],
    holding_service: Annotated[HoldingService, Depends(get_holding_service)],
) -> HoldingResponse:
    """Add a new holding to a portfolio."""
    try:
        # Verify access to portfolio
        portfolio_service.get_portfolio(portfolio_id, user_id)

        holding = holding_service.create_holding(
            portfolio_id=portfolio_id,
            ticker=request.ticker,
            name=request.name,
            asset_type=request.asset_type,
            asset_class=request.asset_class,
            sector=request.sector,
            broker=request.broker,
            quantity=request.quantity,
            purchase_price=request.purchase_price,
            current_price=request.current_price,
            purchase_date=request.purchase_date,
        )
        return HoldingMapper.to_response(holding)
    except PortfolioNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio {portfolio_id} not found",
        )
    except PortfolioAccessDeniedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this portfolio",
        )
    except HoldingValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )


@router.post(
    "/{portfolio_id}/holdings/upload",
    response_model=BulkCreateHoldingsResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload CSV to add holdings",
)
async def upload_holdings(
    portfolio_id: UUID,
    file: UploadFile,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    portfolio_service: Annotated[PortfolioService, Depends(get_portfolio_service)],
    holding_service: Annotated[HoldingService, Depends(get_holding_service)],
) -> BulkCreateHoldingsResponse:
    """Upload a CSV file to bulk add holdings to a portfolio."""
    try:
        # Verify access to portfolio
        portfolio_service.get_portfolio(portfolio_id, user_id)

        if file.content_type not in ("text/csv", "application/csv", "text/plain"):
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="File must be a CSV",
            )

        content = await file.read()
        csv_content = content.decode("utf-8")
        holdings = holding_service.parse_and_create_holdings_from_csv(
            portfolio_id, csv_content
        )
        return HoldingMapper.to_bulk_create_response(holdings)
    except PortfolioNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio {portfolio_id} not found",
        )
    except PortfolioAccessDeniedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this portfolio",
        )
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
    "/{portfolio_id}/holdings/{holding_id}",
    response_model=HoldingResponse,
    summary="Update a holding",
)
def update_holding(
    portfolio_id: UUID,
    holding_id: UUID,
    request: UpdateHoldingRequest,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    portfolio_service: Annotated[PortfolioService, Depends(get_portfolio_service)],
    holding_service: Annotated[HoldingService, Depends(get_holding_service)],
) -> HoldingResponse:
    """Update a holding in a portfolio."""
    try:
        # Verify access to portfolio
        portfolio_service.get_portfolio(portfolio_id, user_id)

        # Verify holding belongs to portfolio
        existing = holding_service.get_holding(holding_id)
        if existing is None or existing.portfolio_id != portfolio_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Holding {holding_id} not found in portfolio",
            )

        updated = holding_service.update_holding(
            holding_id=holding_id,
            ticker=request.ticker,
            name=request.name,
            asset_type=request.asset_type,
            asset_class=request.asset_class,
            sector=request.sector,
            broker=request.broker,
            quantity=request.quantity,
            purchase_price=request.purchase_price,
            current_price=request.current_price,
            purchase_date=request.purchase_date,
        )
        return HoldingMapper.to_response(updated)
    except PortfolioNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio {portfolio_id} not found",
        )
    except PortfolioAccessDeniedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this portfolio",
        )
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
    "/{portfolio_id}/holdings/{holding_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a holding",
)
def delete_holding(
    portfolio_id: UUID,
    holding_id: UUID,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    portfolio_service: Annotated[PortfolioService, Depends(get_portfolio_service)],
    holding_service: Annotated[HoldingService, Depends(get_holding_service)],
) -> None:
    """Delete a holding from a portfolio."""
    try:
        # Verify access to portfolio
        portfolio_service.get_portfolio(portfolio_id, user_id)

        # Verify holding belongs to portfolio
        existing = holding_service.get_holding(holding_id)
        if existing is None or existing.portfolio_id != portfolio_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Holding {holding_id} not found in portfolio",
            )

        holding_service.delete_holding(holding_id)
    except PortfolioNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio {portfolio_id} not found",
        )
    except PortfolioAccessDeniedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this portfolio",
        )
    except HoldingNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Holding {holding_id} not found",
        )


# Risk Analysis
@router.post(
    "/{portfolio_id}/risk-analysis",
    response_model=RiskAnalysisResponse,
    summary="Analyze portfolio risks using AI",
)
def analyze_portfolio_risks(
    portfolio_id: UUID,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    risk_service: Annotated[RiskAnalysisService, Depends(get_risk_analysis_service)],
) -> RiskAnalysisResponse:
    """Generate AI-powered risk analysis for a portfolio.

    Uses LLM with macro economic context to identify:
    - Market risks
    - Concentration risks
    - Sector-specific risks
    - Interest rate risks
    - And more...

    Returns actionable mitigation strategies for each risk.
    """
    try:
        analysis = risk_service.analyze_portfolio_risks(portfolio_id, user_id)
        return RiskAnalysisResponse(
            risks=[
                RiskItem(
                    category=r.get("category", "Unknown"),
                    severity=r.get("severity", "Medium"),
                    title=r.get("title", ""),
                    description=r.get("description", ""),
                    affected_holdings=r.get("affected_holdings", []),
                    potential_impact=r.get("potential_impact", ""),
                    mitigation=r.get("mitigation", ""),
                )
                for r in analysis.risks
            ],
            macro_climate_summary=analysis.macro_climate_summary,
            analysis_timestamp=analysis.analysis_timestamp,
            model_used=analysis.model_used,
        )
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        elif "Access denied" in str(e):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e),
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
