from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from domain.models.security import Security
from domain.services.portfolio_builder_service import PortfolioBuilderService


@pytest.fixture
def mock_ticker_repository():
    """Create a mock ticker repository with sample securities."""
    repo = MagicMock()
    repo.get_all_securities.return_value = [
        Security(
            security_id=uuid4(),
            ticker="AAPL",
            display_name="Apple Inc.",
            asset_type="EQUITY",
            currency="USD",
            sector="Technology",
        ),
        Security(
            security_id=uuid4(),
            ticker="MSFT",
            display_name="Microsoft Corporation",
            asset_type="EQUITY",
            currency="USD",
            sector="Technology",
        ),
        Security(
            security_id=uuid4(),
            ticker="GOOG",
            display_name="Alphabet Inc.",
            asset_type="EQUITY",
            currency="USD",
            sector="Communication Services",
        ),
        Security(
            security_id=uuid4(),
            ticker="JPM",
            display_name="JPMorgan Chase & Co.",
            asset_type="EQUITY",
            currency="USD",
            sector="Financials",
        ),
        Security(
            security_id=uuid4(),
            ticker="VOO",
            display_name="Vanguard S&P 500 ETF",
            asset_type="ETF",
            currency="USD",
            sector="Broad Market",
        ),
        Security(
            security_id=uuid4(),
            ticker="VTI",
            display_name="Vanguard Total Stock Market ETF",
            asset_type="ETF",
            currency="USD",
            sector="Broad Market",
        ),
        Security(
            security_id=uuid4(),
            ticker="BND",
            display_name="Vanguard Total Bond Market ETF",
            asset_type="BOND",
            currency="USD",
            sector="Bonds",
        ),
    ]
    return repo


@pytest.fixture
def portfolio_builder_service(mock_ticker_repository):
    """Create a PortfolioBuilderService with mock dependencies."""
    return PortfolioBuilderService(
        ticker_repository=mock_ticker_repository,
        llm_repository=None,
    )


class TestGenerateRandomAllocation:
    """Tests for random allocation generation."""

    def test_random_allocation_returns_allocations(self, portfolio_builder_service):
        """Should return allocations when securities are available."""
        total_value = Decimal("100000")
        result = portfolio_builder_service.generate_random_allocation(total_value)

        assert len(result.allocations) >= 5
        assert len(result.allocations) <= 6  # max is min(15, len(eligible)) = 6
        assert result.total_value == total_value
        assert len(result.unmatched_descriptions) == 0

    def test_random_allocation_weights_sum_to_100(self, portfolio_builder_service):
        """Weights should sum to exactly 100%."""
        result = portfolio_builder_service.generate_random_allocation(Decimal("100000"))

        total_weight = sum(a.weight for a in result.allocations)
        assert total_weight == Decimal("100")

    def test_random_allocation_values_sum_to_total(self, portfolio_builder_service):
        """Values should sum to approximately the total value."""
        total_value = Decimal("100000")
        result = portfolio_builder_service.generate_random_allocation(total_value)

        total_allocated = sum(a.value for a in result.allocations)
        # Allow small rounding difference
        assert abs(total_allocated - total_value) < Decimal("1")

    def test_random_allocation_minimum_weight(self, portfolio_builder_service):
        """Each allocation should have at least 2% weight."""
        result = portfolio_builder_service.generate_random_allocation(Decimal("100000"))

        for allocation in result.allocations:
            assert allocation.weight >= Decimal("2")

    def test_random_allocation_excludes_bonds(self, portfolio_builder_service):
        """Should only include EQUITY and ETF securities."""
        result = portfolio_builder_service.generate_random_allocation(Decimal("100000"))

        for allocation in result.allocations:
            assert allocation.asset_type in ("EQUITY", "ETF")
            assert allocation.ticker != "BND"

    def test_random_allocation_with_no_securities(self, mock_ticker_repository):
        """Should return empty allocation with error message when no securities."""
        mock_ticker_repository.get_all_securities.return_value = []
        service = PortfolioBuilderService(
            ticker_repository=mock_ticker_repository,
            llm_repository=None,
        )

        result = service.generate_random_allocation(Decimal("100000"))

        assert len(result.allocations) == 0
        assert len(result.unmatched_descriptions) == 1
        assert "No eligible securities" in result.unmatched_descriptions[0]

    def test_random_allocation_with_custom_range(self, portfolio_builder_service):
        """Should respect custom min/max securities range."""
        result = portfolio_builder_service.generate_random_allocation(
            Decimal("50000"),
            min_securities=3,
            max_securities=4,
        )

        assert len(result.allocations) >= 3
        assert len(result.allocations) <= 4


class TestBuildFromDescription:
    """Tests for LLM-based portfolio description interpretation."""

    def test_build_from_description_without_llm(self, portfolio_builder_service):
        """Should return error when LLM repository is not configured."""
        result = portfolio_builder_service.build_from_description(
            description="50% in tech stocks",
            total_value=Decimal("100000"),
        )

        assert len(result.allocations) == 0
        assert "LLM service not available" in result.unmatched_descriptions

    def test_build_from_description_with_llm(self, mock_ticker_repository):
        """Should use LLM to interpret description when available."""
        from domain.ports.llm_repository import (
            AllocationInterpretation,
            PortfolioInterpretation,
            DescriptionClassification,
        )

        mock_llm = MagicMock()
        mock_llm.classify_description.return_value = DescriptionClassification(
            is_portfolio_description=True,
            confidence=0.95,
        )
        mock_llm.interpret_portfolio_description.return_value = PortfolioInterpretation(
            allocations=[
                AllocationInterpretation(
                    ticker="AAPL",
                    display_name="Apple Inc.",
                    weight=Decimal("50"),
                ),
                AllocationInterpretation(
                    ticker="MSFT",
                    display_name="Microsoft Corporation",
                    weight=Decimal("50"),
                ),
            ],
            unmatched_descriptions=[],
            model_used="test-model",
        )

        service = PortfolioBuilderService(
            ticker_repository=mock_ticker_repository,
            llm_repository=mock_llm,
        )

        result = service.build_from_description(
            description="50% Apple, 50% Microsoft",
            total_value=Decimal("100000"),
        )

        assert len(result.allocations) == 2
        assert result.allocations[0].ticker == "AAPL"
        assert result.allocations[0].value == Decimal("50000.00")
        assert result.allocations[1].ticker == "MSFT"
        assert result.allocations[1].value == Decimal("50000.00")

    def test_build_from_description_low_confidence_short_circuits(self, mock_ticker_repository):
        """Should reject descriptions that do not classify as portfolio text."""
        from domain.ports.llm_repository import DescriptionClassification

        mock_llm = MagicMock()
        mock_llm.classify_description.return_value = DescriptionClassification(
            is_portfolio_description=False,
            confidence=0.2,
        )

        service = PortfolioBuilderService(
            ticker_repository=mock_ticker_repository,
            llm_repository=mock_llm,
        )

        result = service.build_from_description(
            description="Tell me a joke about cats",
            total_value=Decimal("100000"),
        )

        assert len(result.allocations) == 0
        assert any("doesn't appear to be about a portfolio" in msg for msg in result.unmatched_descriptions)
        mock_llm.interpret_portfolio_description.assert_not_called()

    def test_build_from_description_rejects_non_portfolio_with_high_confidence(self, mock_ticker_repository):
        """Should reject when is_portfolio_description is False even with high confidence."""
        from domain.ports.llm_repository import DescriptionClassification

        mock_llm = MagicMock()
        mock_llm.classify_description.return_value = DescriptionClassification(
            is_portfolio_description=False,
            confidence=0.99,
        )

        service = PortfolioBuilderService(
            ticker_repository=mock_ticker_repository,
            llm_repository=mock_llm,
        )

        result = service.build_from_description(
            description="This is definitely not a portfolio",
            total_value=Decimal("100000"),
        )

        assert len(result.allocations) == 0
        assert any("doesn't appear to be about a portfolio" in msg for msg in result.unmatched_descriptions)
        mock_llm.interpret_portfolio_description.assert_not_called()


class TestSanitizeDescription:
    """Tests for description sanitization."""

    def test_strips_control_characters(self):
        """Should remove control characters from description."""
        raw = "50% AAPL\x00\x01\x02, 50% MSFT"
        result = PortfolioBuilderService._sanitize_description(raw)
        assert "\x00" not in result
        assert "\x01" not in result
        assert "50% AAPL" in result

    def test_collapses_excess_whitespace(self):
        """Should collapse multiple spaces/newlines into single space."""
        raw = "50%   AAPL\n\n\n50%   MSFT"
        result = PortfolioBuilderService._sanitize_description(raw)
        assert result == "50% AAPL 50% MSFT"

    def test_strips_leading_trailing_whitespace(self):
        """Should strip leading and trailing whitespace."""
        raw = "   50% AAPL   "
        result = PortfolioBuilderService._sanitize_description(raw)
        assert result == "50% AAPL"


class TestGetAvailableSecurities:
    """Tests for getting available securities."""

    def test_get_available_securities(self, portfolio_builder_service, mock_ticker_repository):
        """Should return all securities from repository."""
        result = portfolio_builder_service.get_available_securities()

        assert len(result) == 7
        mock_ticker_repository.get_all_securities.assert_called_once()
