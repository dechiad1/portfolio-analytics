from typing import Annotated

from fastapi import APIRouter, Depends, Query

from domain.commands.compute_analytics import ComputeAnalyticsCommand
from domain.ports.analytics_repository import AnalyticsRepository
from api.schemas.analytics import AnalyticsResponse, TickerSearchResponse, TickerSearchResult
from api.mappers.holding_mapper import HoldingMapper
from dependencies import get_compute_analytics_command, get_analytics_repository

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get(
    "",
    response_model=AnalyticsResponse,
    summary="Get portfolio analytics",
)
def get_analytics(
    command: Annotated[ComputeAnalyticsCommand, Depends(get_compute_analytics_command)],
) -> AnalyticsResponse:
    """Compute and return analytics for all holdings."""
    analytics = command.execute(None)
    return HoldingMapper.analytics_to_response(analytics)


@router.get(
    "/tickers/search",
    response_model=TickerSearchResponse,
    summary="Search for tickers",
)
def search_tickers(
    q: Annotated[str, Query(min_length=1, max_length=50, description="Search query for ticker or name")],
    analytics_repo: Annotated[AnalyticsRepository, Depends(get_analytics_repository)],
    limit: Annotated[int, Query(ge=1, le=100, description="Maximum number of results")] = 20,
) -> TickerSearchResponse:
    """Search for tickers by symbol or name."""
    results = analytics_repo.search_tickers(q, limit)

    return TickerSearchResponse(
        results=[
            TickerSearchResult(
                ticker=fund.ticker,
                name=fund.name,
                asset_class=fund.asset_class,
                category=fund.category,
            )
            for fund in results
        ],
        count=len(results),
    )
