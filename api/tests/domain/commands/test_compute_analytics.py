from datetime import datetime, timezone
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
from domain.models.position import Position
from domain.models.security import Security
from domain.value_objects import FundMetadata, TickerPerformance


def _make_security(ticker="AAPL", name="Apple Inc.", sector="Technology"):
    return Security(
        security_id=uuid4(),
        ticker=ticker,
        display_name=name,
        asset_type="equity",
        currency="USD",
        sector=sector,
    )


def _make_position(ticker="AAPL", name="Apple", sector="Technology"):
    security = _make_security(ticker, name, sector)
    return Position(
        portfolio_id=uuid4(),
        security_id=security.security_id,
        quantity=Decimal("10"),
        avg_cost=Decimal("100"),
        updated_at=datetime.now(timezone.utc),
        security=security,
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
def positions():
    return [
        _make_position("AAPL", "Apple", "Technology"),
        _make_position("BND", "Bond Fund", "Bonds"),
    ]


@pytest.fixture
def mock_position_repository(positions):
    repo = MagicMock()
    repo.get_all.return_value = positions
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
def command(mock_position_repository, mock_analytics_repository):
    return ComputeAnalyticsCommand(
        position_repository=mock_position_repository,
        analytics_repository=mock_analytics_repository,
    )


class TestExecute:
    def test_returns_analytics_for_positions(self, command):
        result = command.execute()
        assert result.holdings_count == 2
        assert len(result.holdings) == 2
        assert result.holdings[0].ticker == "AAPL"

    def test_empty_portfolio(self, command, mock_position_repository):
        mock_position_repository.get_all.return_value = []
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
        # asset_class is "Unknown" for positions since it's not tracked
        assert len(result.asset_class_breakdown) >= 1


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
