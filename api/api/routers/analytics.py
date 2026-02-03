from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, HTTPException

from domain.commands.compute_analytics import ComputeAnalyticsCommand
from domain.ports.analytics_repository import AnalyticsRepository
from api.schemas.analytics import (
    AnalyticsResponse,
    TickerSearchResponse,
    TickerSearchResult,
    SecurityResponse,
    SecuritiesListResponse,
    TickerDetailsResponse,
    TickerPriceResponse,
)
from api.mappers.analytics_mapper import AnalyticsMapper
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
    return AnalyticsMapper.analytics_to_response(analytics)


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


@router.get(
    "/securities",
    response_model=SecuritiesListResponse,
    summary="List all available securities",
)
def list_securities(
    analytics_repo: Annotated[AnalyticsRepository, Depends(get_analytics_repository)],
) -> SecuritiesListResponse:
    """List all available securities with their performance data."""
    securities = analytics_repo.get_all_securities()

    return SecuritiesListResponse(
        securities=[
            SecurityResponse(
                ticker=metadata.ticker,
                name=metadata.name,
                asset_class=metadata.asset_class,
                category=metadata.category,
                expense_ratio=float(metadata.expense_ratio) if metadata.expense_ratio else None,
                # 1-Year metrics
                total_return_1y_pct=float(perf.total_return_1y_pct) if perf and perf.total_return_1y_pct is not None else None,
                return_vs_risk_free_1y_pct=float(perf.return_vs_risk_free_1y_pct) if perf and perf.return_vs_risk_free_1y_pct is not None else None,
                return_vs_sp500_1y_pct=float(perf.return_vs_sp500_1y_pct) if perf and perf.return_vs_sp500_1y_pct is not None else None,
                volatility_1y_pct=float(perf.volatility_1y_pct) if perf and perf.volatility_1y_pct is not None else None,
                sharpe_ratio_1y=float(perf.sharpe_ratio_1y) if perf and perf.sharpe_ratio_1y is not None else None,
                # 5-Year metrics
                total_return_5y_pct=float(perf.total_return_5y_pct) if perf and perf.total_return_5y_pct is not None else None,
                return_vs_risk_free_5y_pct=float(perf.return_vs_risk_free_5y_pct) if perf and perf.return_vs_risk_free_5y_pct is not None else None,
                return_vs_sp500_5y_pct=float(perf.return_vs_sp500_5y_pct) if perf and perf.return_vs_sp500_5y_pct is not None else None,
                volatility_5y_pct=float(perf.volatility_5y_pct) if perf and perf.volatility_5y_pct is not None else None,
                sharpe_ratio_5y=float(perf.sharpe_ratio_5y) if perf and perf.sharpe_ratio_5y is not None else None,
            )
            for metadata, perf in securities
        ],
        count=len(securities),
    )


@router.get(
    "/tickers/{ticker}/details",
    response_model=TickerDetailsResponse,
    summary="Get ticker details with latest price",
)
def get_ticker_details(
    ticker: str,
    analytics_repo: Annotated[AnalyticsRepository, Depends(get_analytics_repository)],
) -> TickerDetailsResponse:
    """Get detailed ticker information including latest price for holding creation."""
    details = analytics_repo.get_ticker_details(ticker)
    if details is None:
        raise HTTPException(status_code=404, detail=f"Ticker {ticker} not found")

    return TickerDetailsResponse(
        ticker=details.ticker,
        name=details.name,
        asset_class=details.asset_class,
        sector=details.sector,
        category=details.category,
        latest_price=float(details.latest_price) if details.latest_price else None,
        latest_price_date=details.latest_price_date,
    )


@router.get(
    "/tickers/{ticker}/price",
    response_model=TickerPriceResponse,
    summary="Get ticker price for a specific date",
)
def get_ticker_price(
    ticker: str,
    price_date: Annotated[date, Query(alias="date", description="Date to get price for (YYYY-MM-DD)")],
    analytics_repo: Annotated[AnalyticsRepository, Depends(get_analytics_repository)],
) -> TickerPriceResponse:
    """Get the price for a ticker at or before a specific date."""
    price_info = analytics_repo.get_price_for_date(ticker, price_date)
    if price_info is None:
        raise HTTPException(
            status_code=404,
            detail=f"No price found for {ticker} on or before {price_date}",
        )

    return TickerPriceResponse(
        ticker=price_info.ticker,
        price_date=price_info.price_date,
        price=float(price_info.price),
    )
