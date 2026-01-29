from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

from domain.models.user import User
from domain.models.risk_analysis import RiskAnalysis
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
from domain.services.portfolio_builder_service import PortfolioBuilderService
from domain.commands.create_portfolio_with_holdings import (
    CreatePortfolioWithHoldingsCommand,
)
from api.schemas.portfolio import (
    CreatePortfolioRequest,
    CreatePortfolioResponse,
    UpdatePortfolioRequest,
    PortfolioResponse,
    PortfolioListResponse,
    PortfolioSummaryResponse,
    AllPortfoliosListResponse,
)
from api.schemas.holding import (
    CreateHoldingRequest,
    UpdateHoldingRequest,
    HoldingResponse,
    HoldingListResponse,
    BulkCreateHoldingsResponse,
)
from api.schemas.risk_analysis import (
    RiskAnalysisResponse,
    RiskItem,
    RiskAnalysisListItem,
    RiskAnalysisListResponse,
)
from api.mappers.portfolio_mapper import PortfolioMapper
from api.mappers.holding_mapper import HoldingMapper
from api.routers.auth import get_current_user_id, get_current_user_full
from domain.services.risk_analysis_service import (
    RiskAnalysisService,
    RiskAnalysisNotFoundError,
    RiskAnalysisAccessDeniedError,
)
from dependencies import (
    get_portfolio_service,
    get_holding_service,
    get_risk_analysis_service,
    get_portfolio_builder_service,
    get_create_portfolio_command,
)

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


@router.get(
    "/all",
    response_model=AllPortfoliosListResponse,
    summary="List all portfolios with user info",
)
def list_all_portfolios(
    current_user: Annotated[User, Depends(get_current_user_full)],
    portfolio_service: Annotated[PortfolioService, Depends(get_portfolio_service)],
) -> AllPortfoliosListResponse:
    """List portfolios with owner email.

    Admin users see all portfolios. Regular users see only their own.
    """
    portfolios_with_users = portfolio_service.get_all_portfolios_with_users(
        user_id=current_user.id,
        is_admin=current_user.is_admin,
    )
    return PortfolioMapper.to_all_portfolios_response(portfolios_with_users)


@router.post(
    "",
    response_model=CreatePortfolioResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a portfolio",
)
def create_portfolio(
    request: CreatePortfolioRequest,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    builder_service: Annotated[PortfolioBuilderService, Depends(get_portfolio_builder_service)],
    create_command: Annotated[
        CreatePortfolioWithHoldingsCommand, Depends(get_create_portfolio_command)
    ],
) -> CreatePortfolioResponse:
    """Create a new portfolio.

    Supports three creation modes:
    - empty: Creates an empty portfolio (default)
    - random: Creates a portfolio with random securities allocation
    - dictation: Creates a portfolio based on natural language description
    """
    allocation = None
    total_value = request.total_value or Decimal("100000")

    if request.creation_mode == "random":
        allocation = builder_service.generate_random_allocation(total_value)

    elif request.creation_mode == "dictation":
        if not request.description:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Description is required for dictation mode",
            )
        allocation = builder_service.build_from_description(
            description=request.description,
            total_value=total_value,
        )

    # Create portfolio and holdings in a single transaction
    result = create_command.execute(
        user_id=user_id,
        name=request.name,
        base_currency=request.base_currency,
        allocation=allocation,
    )

    return CreatePortfolioResponse(
        id=result.portfolio.id,
        user_id=result.portfolio.user_id,
        name=result.portfolio.name,
        base_currency=result.portfolio.base_currency,
        created_at=result.portfolio.created_at,
        updated_at=result.portfolio.updated_at,
        holdings_created=result.holdings_created,
        unmatched_descriptions=result.unmatched_descriptions,
    )


@router.get(
    "/{portfolio_id}",
    response_model=PortfolioResponse,
    summary="Get a portfolio",
)
def get_portfolio(
    portfolio_id: UUID,
    current_user: Annotated[User, Depends(get_current_user_full)],
    portfolio_service: Annotated[PortfolioService, Depends(get_portfolio_service)],
) -> PortfolioResponse:
    """Get a portfolio by ID."""
    try:
        portfolio = portfolio_service.get_portfolio(
            portfolio_id, current_user.id, is_admin=current_user.is_admin
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


@router.put(
    "/{portfolio_id}",
    response_model=PortfolioResponse,
    summary="Update a portfolio",
)
def update_portfolio(
    portfolio_id: UUID,
    request: UpdatePortfolioRequest,
    current_user: Annotated[User, Depends(get_current_user_full)],
    portfolio_service: Annotated[PortfolioService, Depends(get_portfolio_service)],
) -> PortfolioResponse:
    """Update a portfolio."""
    try:
        portfolio = portfolio_service.update_portfolio(
            portfolio_id=portfolio_id,
            user_id=current_user.id,
            name=request.name,
            base_currency=request.base_currency,
            is_admin=current_user.is_admin,
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
    current_user: Annotated[User, Depends(get_current_user_full)],
    portfolio_service: Annotated[PortfolioService, Depends(get_portfolio_service)],
) -> None:
    """Delete a portfolio and all its holdings."""
    try:
        portfolio_service.delete_portfolio(
            portfolio_id, current_user.id, is_admin=current_user.is_admin
        )
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
    current_user: Annotated[User, Depends(get_current_user_full)],
    portfolio_service: Annotated[PortfolioService, Depends(get_portfolio_service)],
) -> PortfolioSummaryResponse:
    """Get portfolio summary with asset type, class, and sector breakdowns."""
    try:
        summary = portfolio_service.get_portfolio_summary(
            portfolio_id, current_user.id, is_admin=current_user.is_admin
        )
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
    current_user: Annotated[User, Depends(get_current_user_full)],
    portfolio_service: Annotated[PortfolioService, Depends(get_portfolio_service)],
) -> HoldingListResponse:
    """List all holdings in a portfolio."""
    try:
        holdings = portfolio_service.get_portfolio_holdings(
            portfolio_id, current_user.id, is_admin=current_user.is_admin
        )
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
    current_user: Annotated[User, Depends(get_current_user_full)],
    portfolio_service: Annotated[PortfolioService, Depends(get_portfolio_service)],
    holding_service: Annotated[HoldingService, Depends(get_holding_service)],
) -> HoldingResponse:
    """Add a new holding to a portfolio."""
    try:
        # Verify access to portfolio
        portfolio_service.get_portfolio(
            portfolio_id, current_user.id, is_admin=current_user.is_admin
        )

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
    current_user: Annotated[User, Depends(get_current_user_full)],
    portfolio_service: Annotated[PortfolioService, Depends(get_portfolio_service)],
    holding_service: Annotated[HoldingService, Depends(get_holding_service)],
) -> BulkCreateHoldingsResponse:
    """Upload a CSV file to bulk add holdings to a portfolio."""
    try:
        # Verify access to portfolio
        portfolio_service.get_portfolio(
            portfolio_id, current_user.id, is_admin=current_user.is_admin
        )

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
    current_user: Annotated[User, Depends(get_current_user_full)],
    portfolio_service: Annotated[PortfolioService, Depends(get_portfolio_service)],
    holding_service: Annotated[HoldingService, Depends(get_holding_service)],
) -> HoldingResponse:
    """Update a holding in a portfolio."""
    try:
        # Verify access to portfolio
        portfolio_service.get_portfolio(
            portfolio_id, current_user.id, is_admin=current_user.is_admin
        )

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
    current_user: Annotated[User, Depends(get_current_user_full)],
    portfolio_service: Annotated[PortfolioService, Depends(get_portfolio_service)],
    holding_service: Annotated[HoldingService, Depends(get_holding_service)],
) -> None:
    """Delete a holding from a portfolio."""
    try:
        # Verify access to portfolio
        portfolio_service.get_portfolio(
            portfolio_id, current_user.id, is_admin=current_user.is_admin
        )

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
    status_code=status.HTTP_201_CREATED,
    summary="Analyze portfolio risks using AI",
)
def analyze_portfolio_risks(
    portfolio_id: UUID,
    current_user: Annotated[User, Depends(get_current_user_full)],
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
    The analysis is persisted and can be retrieved later.
    """
    try:
        analysis = risk_service.analyze_portfolio_risks(
            portfolio_id, current_user.id, is_admin=current_user.is_admin
        )
        return _analysis_to_response(analysis)
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
    "/{portfolio_id}/risk-analyses",
    response_model=RiskAnalysisListResponse,
    summary="List risk analyses for a portfolio",
)
def list_risk_analyses(
    portfolio_id: UUID,
    current_user: Annotated[User, Depends(get_current_user_full)],
    risk_service: Annotated[RiskAnalysisService, Depends(get_risk_analysis_service)],
) -> RiskAnalysisListResponse:
    """List all risk analyses for a portfolio, ordered by date descending."""
    try:
        analyses = risk_service.list_analyses(
            portfolio_id, current_user.id, is_admin=current_user.is_admin
        )
        return RiskAnalysisListResponse(
            analyses=[
                RiskAnalysisListItem(
                    id=a.id,
                    created_at=a.created_at,
                    model_used=a.model_used,
                    risk_count=len(a.risks),
                )
                for a in analyses
            ]
        )
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
    "/{portfolio_id}/risk-analyses/{analysis_id}",
    response_model=RiskAnalysisResponse,
    summary="Get a specific risk analysis",
)
def get_risk_analysis(
    portfolio_id: UUID,
    analysis_id: UUID,
    current_user: Annotated[User, Depends(get_current_user_full)],
    risk_service: Annotated[RiskAnalysisService, Depends(get_risk_analysis_service)],
) -> RiskAnalysisResponse:
    """Get a specific risk analysis by ID."""
    try:
        analysis = risk_service.get_analysis(
            analysis_id, current_user.id, is_admin=current_user.is_admin
        )
        # Verify the analysis belongs to the specified portfolio
        if analysis.portfolio_id != portfolio_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Risk analysis {analysis_id} not found in portfolio {portfolio_id}",
            )
        return _analysis_to_response(analysis)
    except RiskAnalysisNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Risk analysis {analysis_id} not found",
        )
    except RiskAnalysisAccessDeniedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this risk analysis",
        )


@router.delete(
    "/{portfolio_id}/risk-analyses/{analysis_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a risk analysis",
)
def delete_risk_analysis(
    portfolio_id: UUID,
    analysis_id: UUID,
    current_user: Annotated[User, Depends(get_current_user_full)],
    risk_service: Annotated[RiskAnalysisService, Depends(get_risk_analysis_service)],
) -> None:
    """Delete a risk analysis by ID."""
    try:
        # First get the analysis to verify it belongs to the portfolio
        analysis = risk_service.get_analysis(
            analysis_id, current_user.id, is_admin=current_user.is_admin
        )
        if analysis.portfolio_id != portfolio_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Risk analysis {analysis_id} not found in portfolio {portfolio_id}",
            )
        risk_service.delete_analysis(
            analysis_id, current_user.id, is_admin=current_user.is_admin
        )
    except RiskAnalysisNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Risk analysis {analysis_id} not found",
        )
    except RiskAnalysisAccessDeniedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this risk analysis",
        )


def _analysis_to_response(analysis: RiskAnalysis) -> RiskAnalysisResponse:
    """Convert a RiskAnalysis domain model to a response."""
    return RiskAnalysisResponse(
        id=analysis.id,
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
        created_at=analysis.created_at,
        model_used=analysis.model_used,
    )
