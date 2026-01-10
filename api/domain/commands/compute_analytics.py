from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from domain.models.holding import Holding
from domain.ports.analytics_repository import (
    AnalyticsRepository,
    FundMetadata,
    TickerPerformance,
)
from domain.ports.holding_repository import HoldingRepository


class HoldingAnalytics(BaseModel):
    """Analytics for a single holding."""

    ticker: str
    name: str
    asset_class: str
    sector: str
    broker: str
    purchase_date: date
    latest_return: Decimal | None = None
    cumulative_return: Decimal | None = None
    volatility: Decimal | None = None
    expense_ratio: Decimal | None = None
    category: str | None = None

    model_config = {"frozen": True}


class PortfolioAnalytics(BaseModel):
    """Aggregated portfolio analytics."""

    session_id: UUID
    total_holdings: int
    holdings: list[HoldingAnalytics]
    portfolio_avg_return: Decimal | None = None
    portfolio_avg_volatility: Decimal | None = None
    asset_class_breakdown: dict[str, int]
    sector_breakdown: dict[str, int]
    broker_breakdown: dict[str, int]

    model_config = {"frozen": True}


class ComputeAnalyticsCommand:
    """Command to compute portfolio analytics for a session."""

    def __init__(
        self,
        holding_repository: HoldingRepository,
        analytics_repository: AnalyticsRepository,
    ) -> None:
        self._holding_repository = holding_repository
        self._analytics_repository = analytics_repository

    def execute(self, session_id: UUID) -> PortfolioAnalytics:
        """Compute and return analytics for the session's holdings."""
        holdings = self._holding_repository.get_by_session_id(session_id)

        if not holdings:
            return PortfolioAnalytics(
                session_id=session_id,
                total_holdings=0,
                holdings=[],
                portfolio_avg_return=None,
                portfolio_avg_volatility=None,
                asset_class_breakdown={},
                sector_breakdown={},
                broker_breakdown={},
            )

        tickers = list({h.ticker for h in holdings})

        performance_data = self._analytics_repository.get_performance_for_tickers(
            tickers
        )
        metadata = self._analytics_repository.get_fund_metadata_for_tickers(tickers)

        performance_by_ticker = self._index_performance_by_ticker(performance_data)
        metadata_by_ticker = self._index_metadata_by_ticker(metadata)

        holding_analytics = self._build_holding_analytics(
            holdings, performance_by_ticker, metadata_by_ticker
        )

        portfolio_metrics = self._compute_portfolio_metrics(holding_analytics)
        breakdowns = self._compute_breakdowns(holdings)

        return PortfolioAnalytics(
            session_id=session_id,
            total_holdings=len(holdings),
            holdings=holding_analytics,
            portfolio_avg_return=portfolio_metrics["avg_return"],
            portfolio_avg_volatility=portfolio_metrics["avg_volatility"],
            asset_class_breakdown=breakdowns["asset_class"],
            sector_breakdown=breakdowns["sector"],
            broker_breakdown=breakdowns["broker"],
        )

    def _index_performance_by_ticker(
        self, performance_data: list[TickerPerformance]
    ) -> dict[str, TickerPerformance]:
        """Get the latest performance record for each ticker."""
        latest: dict[str, TickerPerformance] = {}
        for perf in performance_data:
            if perf.ticker not in latest or perf.date > latest[perf.ticker].date:
                latest[perf.ticker] = perf
        return latest

    def _index_metadata_by_ticker(
        self, metadata: list[FundMetadata]
    ) -> dict[str, FundMetadata]:
        """Index metadata by ticker."""
        return {m.ticker: m for m in metadata}

    def _build_holding_analytics(
        self,
        holdings: list[Holding],
        performance_by_ticker: dict[str, TickerPerformance],
        metadata_by_ticker: dict[str, FundMetadata],
    ) -> list[HoldingAnalytics]:
        """Build analytics for each holding."""
        result: list[HoldingAnalytics] = []

        for holding in holdings:
            perf = performance_by_ticker.get(holding.ticker)
            meta = metadata_by_ticker.get(holding.ticker)

            analytics = HoldingAnalytics(
                ticker=holding.ticker,
                name=holding.name,
                asset_class=holding.asset_class,
                sector=holding.sector,
                broker=holding.broker,
                purchase_date=holding.purchase_date,
                latest_return=perf.daily_return if perf else None,
                cumulative_return=perf.cumulative_return if perf else None,
                volatility=perf.volatility if perf else None,
                expense_ratio=meta.expense_ratio if meta else None,
                category=meta.category if meta else None,
            )
            result.append(analytics)

        return result

    def _compute_portfolio_metrics(
        self, holding_analytics: list[HoldingAnalytics]
    ) -> dict[str, Decimal | None]:
        """Compute portfolio-level aggregate metrics."""
        returns = [h.cumulative_return for h in holding_analytics if h.cumulative_return]
        volatilities = [h.volatility for h in holding_analytics if h.volatility]

        avg_return = None
        if returns:
            avg_return = sum(returns) / len(returns)

        avg_volatility = None
        if volatilities:
            avg_volatility = sum(volatilities) / len(volatilities)

        return {"avg_return": avg_return, "avg_volatility": avg_volatility}

    def _compute_breakdowns(
        self, holdings: list[Holding]
    ) -> dict[str, dict[str, int]]:
        """Compute breakdown counts by various dimensions."""
        asset_class: dict[str, int] = {}
        sector: dict[str, int] = {}
        broker: dict[str, int] = {}

        for holding in holdings:
            asset_class[holding.asset_class] = (
                asset_class.get(holding.asset_class, 0) + 1
            )
            sector[holding.sector] = sector.get(holding.sector, 0) + 1
            broker[holding.broker] = broker.get(holding.broker, 0) + 1

        return {
            "asset_class": asset_class,
            "sector": sector,
            "broker": broker,
        }
