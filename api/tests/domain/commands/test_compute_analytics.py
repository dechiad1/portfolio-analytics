from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from domain.commands.compute_analytics import (
    AssetClassBreakdown,
    ComputeAnalyticsCommand,
    PortfolioAnalytics,
    SectorBreakdown,
    TickerAnalytics,
)
from domain.models.holding import Holding
from domain.value_objects import FundMetadata, TickerPerformance


def _make_holding(ticker="AAPL", name="Apple", asset_class="US Large Cap", sector="Technology"):
    return Holding(
        id=uuid4(),
        portfolio_id=uuid4(),
        ticker=ticker,
        name=name,
        asset_type="equity",
        asset_class=asset_class,
        sector=sector,
        broker="Test",
        quantity=Decimal("10"),
        purchase_price=Decimal("100"),
        current_price=Decimal("150"),
        purchase_date=date(2024, 1, 1),
        created_at=datetime.now(timezone.utc),
    )


def _make_performance(ticker="AAPL", total_return=Decimal("25.0")):
    return TickerPerformance(
        ticker=ticker,
        total_return_pct=total_return,
        annualized_return_pct=Decimal("12.0"),
        volatility_pct=Decimal("15.0"),
        sharpe_ratio=Decimal("1.2"),
        vs_benchmark_pct=Decimal("3.0"),
    )


def _make_metadata(ticker="AAPL"):
    return FundMetadata(
        ticker=ticker,
        name="Apple Inc.",
        asset_class="US Large Cap",
        expense_ratio=Decimal("0.03"),
    )


@pytest.fixture
def holdings():
    return [
        _make_holding("AAPL", "Apple", "US Large Cap", "Technology"),
        _make_holding("BND", "Bond Fund", "Bonds", "Bonds"),
    ]


@pytest.fixture
def mock_holding_repository(holdings):
    repo = MagicMock()
    repo.get_all.return_value = holdings
    return repo


@pytest.fixture
def mock_analytics_repository():
    repo = MagicMock()
    repo.get_performance_for_tickers.return_value = [
        _make_performance("AAPL", Decimal("25.0")),
        _make_performance("BND", Decimal("5.0")),
    ]
    repo.get_fund_metadata_for_tickers.return_value = [
        _make_metadata("AAPL"),
        _make_metadata("BND"),
    ]
    return repo


@pytest.fixture
def command(mock_holding_repository, mock_analytics_repository):
    return ComputeAnalyticsCommand(
        holding_repository=mock_holding_repository,
        analytics_repository=mock_analytics_repository,
    )


class TestExecute:
    def test_returns_analytics_for_holdings(self, command):
        result = command.execute()
        assert result.holdings_count == 2
        assert len(result.holdings) == 2
        assert result.holdings[0].ticker == "AAPL"

    def test_empty_portfolio(self, command, mock_holding_repository):
        mock_holding_repository.get_all.return_value = []
        result = command.execute()
        assert result.holdings_count == 0
        assert result.holdings == []
        assert result.asset_class_breakdown == []

    def test_computes_averages(self, command):
        result = command.execute()
        # avg of 25.0 and 5.0 = 15.0
        assert result.avg_total_return_pct == 15.0

    def test_beat_benchmark_count(self, command):
        result = command.execute()
        # Both have vs_benchmark_pct = 3.0 > 0
        assert result.beat_benchmark_count == 2


class TestAssetClassBreakdown:
    def test_groups_by_asset_class(self, command):
        result = command.execute()
        assert len(result.asset_class_breakdown) == 2
        classes = {b.asset_class for b in result.asset_class_breakdown}
        assert "US Large Cap" in classes
        assert "Bonds" in classes


class TestSectorBreakdown:
    def test_groups_by_sector(self, command):
        result = command.execute()
        assert len(result.sector_breakdown) == 2
        sectors = {b.sector for b in result.sector_breakdown}
        assert "Technology" in sectors
        assert "Bonds" in sectors


class TestBuildTickerAnalytics:
    def test_handles_missing_performance(self, command, mock_analytics_repository):
        mock_analytics_repository.get_performance_for_tickers.return_value = []
        result = command.execute()
        assert result.holdings[0].total_return_pct == 0.0

    def test_handles_missing_metadata(self, command, mock_analytics_repository):
        mock_analytics_repository.get_fund_metadata_for_tickers.return_value = []
        result = command.execute()
        assert result.holdings[0].expense_ratio is None
