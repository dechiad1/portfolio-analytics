from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from domain.models.user import User
from domain.models.risk_analysis import RiskAnalysis
from domain.services.portfolio_service import (
    PortfolioService,
    PortfolioNotFoundError,
    PortfolioAccessDeniedError,
)
from domain.services.position_service import (
    PositionService,
    PositionNotFoundError,
)
from domain.ports.ticker_repository import TickerRepository
from domain.services.transaction_service import TransactionService
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
from api.schemas.risk_analysis import (
    RiskAnalysisResponse,
    RiskItem,
    RiskAnalysisListItem,
    RiskAnalysisListResponse,
)
from api.schemas.position import (
    AddPositionRequest,
    PositionResponse,
    PositionListResponse,
    TransactionResponse,
    TransactionListResponse,
)
from api.mappers.portfolio_mapper import PortfolioMapper
from api.routers.auth import get_current_user_id, get_current_user_full
from domain.services.risk_analysis_service import (
    RiskAnalysisService,
    RiskAnalysisNotFoundError,
    RiskAnalysisAccessDeniedError,
)
from dependencies import (
    get_portfolio_service,
    get_risk_analysis_service,
    get_portfolio_builder_service,
    get_create_portfolio_command,
    get_position_service,
    get_transaction_service,
    get_ticker_repository,
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


# Positions
@router.get(
    "/{portfolio_id}/positions",
    response_model=PositionListResponse,
    summary="List portfolio positions",
)
def list_positions(
    portfolio_id: UUID,
    current_user: Annotated[User, Depends(get_current_user_full)],
    portfolio_service: Annotated[PortfolioService, Depends(get_portfolio_service)],
    position_service: Annotated[PositionService, Depends(get_position_service)],
) -> PositionListResponse:
    """List all positions in a portfolio with security info."""
    try:
        # Verify access to portfolio
        portfolio_service.get_portfolio(
            portfolio_id, current_user.id, is_admin=current_user.is_admin
        )
        positions = position_service.get_portfolio_positions(portfolio_id)
        return PositionListResponse(
            positions=[_position_to_response(p) for p in positions],
            count=len(positions),
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


@router.post(
    "/{portfolio_id}/positions",
    response_model=PositionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add position to portfolio",
)
def add_position(
    portfolio_id: UUID,
    request: AddPositionRequest,
    current_user: Annotated[User, Depends(get_current_user_full)],
    portfolio_service: Annotated[PortfolioService, Depends(get_portfolio_service)],
    position_service: Annotated[PositionService, Depends(get_position_service)],
    ticker_repository: Annotated[TickerRepository, Depends(get_ticker_repository)],
) -> PositionResponse:
    """Add a position to a portfolio by creating a BUY transaction."""
    try:
        # Verify access to portfolio
        portfolio_service.get_portfolio(
            portfolio_id, current_user.id, is_admin=current_user.is_admin
        )

        # Look up security_id from ticker
        security_id = ticker_repository.get_security_id_by_ticker(request.ticker)
        if security_id is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Security with ticker '{request.ticker}' not found",
            )

        position = position_service.add_position(
            portfolio_id=portfolio_id,
            security_id=security_id,
            quantity=request.quantity,
            price=request.price,
            event_date=request.event_date,
        )

        # Re-fetch to get enriched security data
        enriched = position_service.get_position(portfolio_id, security_id)
        return _position_to_response(enriched or position)

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
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )


@router.delete(
    "/{portfolio_id}/positions/{security_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a position",
)
def remove_position(
    portfolio_id: UUID,
    security_id: UUID,
    current_user: Annotated[User, Depends(get_current_user_full)],
    portfolio_service: Annotated[PortfolioService, Depends(get_portfolio_service)],
    position_service: Annotated[PositionService, Depends(get_position_service)],
) -> None:
    """Remove a position by creating a SELL transaction for the full quantity."""
    try:
        # Verify access to portfolio
        portfolio_service.get_portfolio(
            portfolio_id, current_user.id, is_admin=current_user.is_admin
        )
        position_service.remove_position(portfolio_id, security_id)
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
    except PositionNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Position for security {security_id} not found",
        )


# Transactions
@router.get(
    "/{portfolio_id}/transactions",
    response_model=TransactionListResponse,
    summary="List portfolio transactions",
)
def list_transactions(
    portfolio_id: UUID,
    current_user: Annotated[User, Depends(get_current_user_full)],
    portfolio_service: Annotated[PortfolioService, Depends(get_portfolio_service)],
    transaction_service: Annotated[TransactionService, Depends(get_transaction_service)],
) -> TransactionListResponse:
    """List all transactions for a portfolio."""
    try:
        # Verify access to portfolio
        portfolio_service.get_portfolio(
            portfolio_id, current_user.id, is_admin=current_user.is_admin
        )
        transactions = transaction_service.get_portfolio_transactions(portfolio_id)
        return TransactionListResponse(
            transactions=[_transaction_to_response(t) for t in transactions],
            count=len(transactions),
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


def _position_to_response(position) -> PositionResponse:
    """Convert a Position domain model to a response."""
    return PositionResponse(
        portfolio_id=str(position.portfolio_id),
        security_id=str(position.security_id),
        ticker=position.security.ticker if position.security else "UNKNOWN",
        name=position.security.display_name if position.security else "Unknown",
        asset_type=position.security.asset_type if position.security else "equity",
        sector=position.security.sector if position.security else None,
        quantity=float(position.quantity),
        avg_cost=float(position.avg_cost),
        current_price=float(position.current_price) if position.current_price else None,
        market_value=float(position.market_value) if position.market_value else None,
        cost_basis=float(position.cost_basis),
        gain_loss=float(position.gain_loss) if position.gain_loss else None,
        gain_loss_pct=float(position.gain_loss_pct) if position.gain_loss_pct else None,
    )


def _transaction_to_response(transaction) -> TransactionResponse:
    """Convert a Transaction domain model to a response."""
    return TransactionResponse(
        txn_id=str(transaction.txn_id),
        portfolio_id=str(transaction.portfolio_id),
        security_id=str(transaction.security_id) if transaction.security_id else None,
        txn_type=transaction.txn_type.value,
        quantity=float(transaction.quantity),
        price=float(transaction.price) if transaction.price else None,
        fees=float(transaction.fees),
        event_ts=transaction.event_ts,
        notes=transaction.notes,
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
