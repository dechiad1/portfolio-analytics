import json
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from adapters.llm.anthropic_repository import AnthropicLLMRepository
from domain.ports.llm_repository import SecuritySummary


@pytest.fixture
def repo():
    """Create an AnthropicLLMRepository with a fake API key."""
    with patch("adapters.llm.anthropic_repository.anthropic.Anthropic"):
        return AnthropicLLMRepository(api_key="fake-key")


class TestClassifyDescription:
    """Tests for classify_description."""

    def test_returns_high_confidence_for_portfolio_text(self, repo):
        """Should return high confidence for portfolio descriptions."""
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(text='{"is_portfolio_description": true, "confidence": 0.95}')
        ]
        repo._client.messages.create.return_value = mock_response

        result = repo.classify_description("50% stocks, 30% bonds, 20% cash")

        assert result.is_portfolio_description is True
        assert result.confidence == 0.95

    def test_returns_low_confidence_for_non_portfolio_text(self, repo):
        """Should return low confidence for unrelated text."""
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(text='{"is_portfolio_description": false, "confidence": 0.1}')
        ]
        repo._client.messages.create.return_value = mock_response

        result = repo.classify_description("Tell me a joke")

        assert result.is_portfolio_description is False
        assert result.confidence == 0.1

    def test_returns_zero_confidence_on_parse_failure(self, repo):
        """Should default to zero confidence when JSON parsing fails."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="not json")]
        repo._client.messages.create.return_value = mock_response

        result = repo.classify_description("anything")

        assert result.confidence == 0.0
        assert result.is_portfolio_description is False


class TestWeightBoundsFiltering:
    """Tests for weight bounds filtering in interpret_portfolio_description."""

    def test_skips_zero_weight_allocations(self, repo):
        """Should skip allocations with weight <= 0."""
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                text=json.dumps(
                    {
                        "allocations": [
                            {"ticker": "AAPL", "display_name": "Apple", "weight": 0},
                            {"ticker": "MSFT", "display_name": "Microsoft", "weight": 100},
                        ],
                        "unmatched_descriptions": [],
                    }
                )
            )
        ]
        repo._client.messages.create.return_value = mock_response

        result = repo.interpret_portfolio_description("test", [])

        assert len(result.allocations) == 1
        assert result.allocations[0].ticker == "MSFT"

    def test_skips_negative_weight_allocations(self, repo):
        """Should skip allocations with negative weight."""
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                text=json.dumps(
                    {
                        "allocations": [
                            {"ticker": "AAPL", "display_name": "Apple", "weight": -10},
                            {"ticker": "MSFT", "display_name": "Microsoft", "weight": 50},
                        ],
                        "unmatched_descriptions": [],
                    }
                )
            )
        ]
        repo._client.messages.create.return_value = mock_response

        result = repo.interpret_portfolio_description("test", [])

        assert len(result.allocations) == 1
        assert result.allocations[0].ticker == "MSFT"

    def test_skips_over_100_weight_allocations(self, repo):
        """Should skip allocations with weight > 100."""
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                text=json.dumps(
                    {
                        "allocations": [
                            {"ticker": "AAPL", "display_name": "Apple", "weight": 150},
                            {"ticker": "MSFT", "display_name": "Microsoft", "weight": 50},
                        ],
                        "unmatched_descriptions": [],
                    }
                )
            )
        ]
        repo._client.messages.create.return_value = mock_response

        result = repo.interpret_portfolio_description("test", [])

        assert len(result.allocations) == 1
        assert result.allocations[0].ticker == "MSFT"
