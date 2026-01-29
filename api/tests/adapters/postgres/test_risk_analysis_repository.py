from contextlib import contextmanager
from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from domain.models.risk_analysis import RiskAnalysis
from adapters.postgres.risk_analysis_repository import PostgresRiskAnalysisRepository


@pytest.fixture
def mock_cursor():
    """Create a mock cursor."""
    return MagicMock()


@pytest.fixture
def mock_pool(mock_cursor):
    """Create a mock connection pool with cursor context manager."""
    pool = MagicMock()

    @contextmanager
    def cursor_context():
        yield mock_cursor

    pool.cursor = cursor_context
    return pool


@pytest.fixture
def repository(mock_pool):
    """Create repository with mocked pool."""
    return PostgresRiskAnalysisRepository(mock_pool)


@pytest.fixture
def sample_analysis():
    """Create a sample RiskAnalysis for testing."""
    return RiskAnalysis(
        id=uuid4(),
        portfolio_id=uuid4(),
        risks=[
            {"category": "Market", "severity": "High", "title": "Test Risk"}
        ],
        macro_climate_summary="Test summary",
        model_used="test-model",
        created_at=datetime.now(timezone.utc),
    )


class TestPostgresRiskAnalysisRepositoryCreate:
    """Tests for create method."""

    def test_create_executes_insert(
        self,
        repository,
        mock_cursor,
        sample_analysis,
    ):
        """Should execute INSERT with correct parameters."""
        mock_cursor.fetchone.return_value = (
            sample_analysis.id,
            sample_analysis.portfolio_id,
            sample_analysis.risks,
            sample_analysis.macro_climate_summary,
            sample_analysis.model_used,
            sample_analysis.created_at,
        )

        result = repository.create(sample_analysis)

        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args
        assert "INSERT INTO risk_analysis" in call_args[0][0]
        assert result.id == sample_analysis.id

    def test_create_raises_when_insert_fails(
        self,
        repository,
        mock_cursor,
        sample_analysis,
    ):
        """Should raise RuntimeError when insert fails."""
        mock_cursor.fetchone.return_value = None

        with pytest.raises(RuntimeError, match="Failed to create"):
            repository.create(sample_analysis)


class TestPostgresRiskAnalysisRepositoryGetById:
    """Tests for get_by_id method."""

    def test_get_by_id_returns_analysis(
        self,
        repository,
        mock_cursor,
        sample_analysis,
    ):
        """Should return analysis when found."""
        mock_cursor.fetchone.return_value = (
            sample_analysis.id,
            sample_analysis.portfolio_id,
            sample_analysis.risks,
            sample_analysis.macro_climate_summary,
            sample_analysis.model_used,
            sample_analysis.created_at,
        )

        result = repository.get_by_id(sample_analysis.id)

        assert result is not None
        assert result.id == sample_analysis.id

    def test_get_by_id_returns_none_when_not_found(
        self,
        repository,
        mock_cursor,
    ):
        """Should return None when analysis not found."""
        mock_cursor.fetchone.return_value = None

        result = repository.get_by_id(uuid4())

        assert result is None


class TestPostgresRiskAnalysisRepositoryGetByPortfolioId:
    """Tests for get_by_portfolio_id method."""

    def test_get_by_portfolio_id_returns_list(
        self,
        repository,
        mock_cursor,
    ):
        """Should return list of analyses."""
        portfolio_id = uuid4()
        analyses_data = [
            (
                uuid4(),
                portfolio_id,
                [{"risk": "test"}],
                "Summary 1",
                "model-1",
                datetime.now(timezone.utc),
            ),
            (
                uuid4(),
                portfolio_id,
                [{"risk": "test2"}],
                "Summary 2",
                "model-2",
                datetime.now(timezone.utc),
            ),
        ]
        mock_cursor.fetchall.return_value = analyses_data

        result = repository.get_by_portfolio_id(portfolio_id)

        assert len(result) == 2
        assert all(a.portfolio_id == portfolio_id for a in result)

    def test_get_by_portfolio_id_returns_empty_list_when_none(
        self,
        repository,
        mock_cursor,
    ):
        """Should return empty list when no analyses found."""
        mock_cursor.fetchall.return_value = []

        result = repository.get_by_portfolio_id(uuid4())

        assert result == []


class TestPostgresRiskAnalysisRepositoryDelete:
    """Tests for delete method."""

    def test_delete_returns_true_when_deleted(
        self,
        repository,
        mock_cursor,
    ):
        """Should return True when deletion succeeds."""
        analysis_id = uuid4()
        mock_cursor.fetchone.return_value = (analysis_id,)

        result = repository.delete(analysis_id)

        assert result is True

    def test_delete_returns_false_when_not_found(
        self,
        repository,
        mock_cursor,
    ):
        """Should return False when analysis not found."""
        mock_cursor.fetchone.return_value = None

        result = repository.delete(uuid4())

        assert result is False


class TestPostgresRiskAnalysisRepositoryGetPortfolioIdForAnalysis:
    """Tests for get_portfolio_id_for_analysis method."""

    def test_get_portfolio_id_for_analysis_returns_id(
        self,
        repository,
        mock_cursor,
    ):
        """Should return portfolio_id when analysis exists."""
        analysis_id = uuid4()
        portfolio_id = uuid4()
        mock_cursor.fetchone.return_value = (portfolio_id,)

        result = repository.get_portfolio_id_for_analysis(analysis_id)

        assert result == portfolio_id

    def test_get_portfolio_id_for_analysis_returns_none_when_not_found(
        self,
        repository,
        mock_cursor,
    ):
        """Should return None when analysis not found."""
        mock_cursor.fetchone.return_value = None

        result = repository.get_portfolio_id_for_analysis(uuid4())

        assert result is None
