from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from domain.models.holding import Holding
from domain.models.portfolio import Portfolio
from domain.ports.llm_repository import RiskAnalysis
from domain.services.risk_analysis_service import (
    LLM_UNAVAILABLE_MESSAGE,
    RiskAnalysisService,
)


@pytest.fixture
def user_id():
    return uuid4()


@pytest.fixture
def portfolio_id():
    return uuid4()


@pytest.fixture
def mock_portfolio(portfolio_id, user_id):
    return Portfolio(
        id=portfolio_id,
        user_id=user_id,
        name="Test Portfolio",
        base_currency="USD",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def mock_holdings(portfolio_id):
    return [
        Holding(
            id=uuid4(),
            portfolio_id=portfolio_id,
            ticker="AAPL",
            name="Apple Inc.",
            asset_type="EQUITY",
            asset_class="US Large Cap",
            sector="Technology",
            broker="Test Broker",
            quantity=Decimal("10"),
            purchase_price=Decimal("150.00"),
            current_price=Decimal("175.00"),
            purchase_date=date(2024, 1, 1),
            created_at=datetime.now(timezone.utc),
        ),
        Holding(
            id=uuid4(),
            portfolio_id=portfolio_id,
            ticker="MSFT",
            name="Microsoft Corporation",
            asset_type="EQUITY",
            asset_class="US Large Cap",
            sector="Technology",
            broker="Test Broker",
            quantity=Decimal("5"),
            purchase_price=Decimal("300.00"),
            current_price=Decimal("350.00"),
            purchase_date=date(2024, 1, 1),
            created_at=datetime.now(timezone.utc),
        ),
    ]


@pytest.fixture
def mock_portfolio_repository(mock_portfolio):
    repo = MagicMock()
    repo.get_by_id.return_value = mock_portfolio
    return repo


@pytest.fixture
def mock_holding_repository(mock_holdings):
    repo = MagicMock()
    repo.get_by_portfolio_id.return_value = mock_holdings
    return repo


@pytest.fixture
def mock_llm_repository():
    repo = MagicMock()
    repo.analyze_portfolio_risks.return_value = RiskAnalysis(
        risks=[{"risk": "Concentration risk", "severity": "medium"}],
        macro_climate_summary="Markets are volatile.",
        analysis_timestamp=datetime.now(timezone.utc).isoformat(),
        model_used="claude-3-sonnet",
    )
    return repo


class TestRiskAnalysisServiceWithNullLLM:
    """Tests for RiskAnalysisService when LLM repository is None."""

    def test_returns_fallback_when_llm_unavailable(
        self,
        portfolio_id,
        user_id,
        mock_portfolio_repository,
        mock_holding_repository,
    ):
        """When LLM repository is None, should return fallback RiskAnalysis."""
        service = RiskAnalysisService(
            llm_repository=None,
            portfolio_repository=mock_portfolio_repository,
            holding_repository=mock_holding_repository,
        )

        result = service.analyze_portfolio_risks(portfolio_id, user_id)

        assert result.risks == []
        assert result.macro_climate_summary == LLM_UNAVAILABLE_MESSAGE
        assert result.model_used == "unavailable"
        assert result.analysis_timestamp is not None

    def test_does_not_call_llm_when_unavailable(
        self,
        portfolio_id,
        user_id,
        mock_portfolio_repository,
        mock_holding_repository,
    ):
        """When LLM is None, should not attempt to call LLM methods."""
        service = RiskAnalysisService(
            llm_repository=None,
            portfolio_repository=mock_portfolio_repository,
            holding_repository=mock_holding_repository,
        )

        # Should not raise AttributeError
        result = service.analyze_portfolio_risks(portfolio_id, user_id)

        assert result is not None


class TestRiskAnalysisServiceWithLLM:
    """Tests for RiskAnalysisService when LLM repository is available."""

    def test_calls_llm_when_available(
        self,
        portfolio_id,
        user_id,
        mock_portfolio_repository,
        mock_holding_repository,
        mock_llm_repository,
    ):
        """When LLM repository is available, should call it for analysis."""
        service = RiskAnalysisService(
            llm_repository=mock_llm_repository,
            portfolio_repository=mock_portfolio_repository,
            holding_repository=mock_holding_repository,
        )

        result = service.analyze_portfolio_risks(portfolio_id, user_id)

        mock_llm_repository.analyze_portfolio_risks.assert_called_once()
        assert result.risks == [{"risk": "Concentration risk", "severity": "medium"}]
        assert result.model_used == "claude-3-sonnet"


class TestRiskAnalysisServiceAccessControl:
    """Tests for portfolio access control in RiskAnalysisService."""

    def test_raises_when_portfolio_not_found(
        self,
        portfolio_id,
        user_id,
        mock_holding_repository,
    ):
        """Should raise ValueError when portfolio does not exist."""
        portfolio_repo = MagicMock()
        portfolio_repo.get_by_id.return_value = None

        service = RiskAnalysisService(
            llm_repository=None,
            portfolio_repository=portfolio_repo,
            holding_repository=mock_holding_repository,
        )

        with pytest.raises(ValueError, match="not found"):
            service.analyze_portfolio_risks(portfolio_id, user_id)

    def test_raises_when_user_not_owner(
        self,
        portfolio_id,
        mock_portfolio,
        mock_holding_repository,
    ):
        """Should raise ValueError when user is not the portfolio owner."""
        other_user_id = uuid4()
        portfolio_repo = MagicMock()
        portfolio_repo.get_by_id.return_value = mock_portfolio

        service = RiskAnalysisService(
            llm_repository=None,
            portfolio_repository=portfolio_repo,
            holding_repository=mock_holding_repository,
        )

        with pytest.raises(ValueError, match="Access denied"):
            service.analyze_portfolio_risks(portfolio_id, other_user_id)

    def test_admin_can_access_any_portfolio(
        self,
        portfolio_id,
        mock_portfolio,
        mock_portfolio_repository,
        mock_holding_repository,
    ):
        """Admin users should be able to access any portfolio."""
        other_user_id = uuid4()

        service = RiskAnalysisService(
            llm_repository=None,
            portfolio_repository=mock_portfolio_repository,
            holding_repository=mock_holding_repository,
        )

        # Should not raise even though user_id doesn't match
        result = service.analyze_portfolio_risks(
            portfolio_id, other_user_id, is_admin=True
        )

        assert result is not None
