"""Tests for the simulation API endpoint data contracts."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from api.schemas.simulation import (
    SimulationRequest,
    SimulationResponse,
    SimulationSummaryResponse,
    MetricsSummaryResponse,
    SamplePathResponse,
    ModelType,
    MuType,
    ScenarioType,
    RebalanceFrequency,
    RuinThresholdType,
)


class TestRequestValidation:
    """Tests for request validation."""

    def test_request_with_defaults(self):
        """Verify request with all defaults is valid."""
        request = SimulationRequest()
        assert request.horizon_years == 5
        assert request.num_paths == 1000
        assert request.model_type == ModelType.GAUSSIAN
        assert request.scenario is None
        assert request.rebalance_frequency is None
        assert request.mu_type == MuType.HISTORICAL
        assert request.sample_paths_count == 10
        assert request.ruin_threshold is None
        assert request.ruin_threshold_type == RuinThresholdType.PERCENTAGE

    def test_request_with_all_fields(self):
        """Verify request with all fields set is valid."""
        request = SimulationRequest(
            horizon_years=10,
            num_paths=5000,
            model_type=ModelType.STUDENT_T,
            scenario=ScenarioType.JAPAN_LOST_DECADE,
            rebalance_frequency=RebalanceFrequency.QUARTERLY,
            mu_type=MuType.FORWARD,
            sample_paths_count=25,
            ruin_threshold=0.30,
            ruin_threshold_type=RuinThresholdType.PERCENTAGE,
        )
        assert request.horizon_years == 10
        assert request.num_paths == 5000
        assert request.model_type == ModelType.STUDENT_T
        assert request.scenario == ScenarioType.JAPAN_LOST_DECADE

    def test_request_enum_values(self):
        """Verify all enum values are valid."""
        # Model types
        for model in ["gaussian", "student_t", "regime_switching"]:
            request = SimulationRequest(model_type=model)
            assert request.model_type.value == model

        # Scenarios
        for scenario in ["japan_lost_decade", "stagflation"]:
            request = SimulationRequest(scenario=scenario)
            assert request.scenario.value == scenario

        # Rebalance frequencies
        for freq in ["quarterly", "monthly"]:
            request = SimulationRequest(rebalance_frequency=freq)
            assert request.rebalance_frequency.value == freq

        # Mu types
        for mu in ["historical", "forward"]:
            request = SimulationRequest(mu_type=mu)
            assert request.mu_type.value == mu

        # Ruin threshold types
        for ruin_type in ["percentage", "absolute"]:
            request = SimulationRequest(ruin_threshold_type=ruin_type)
            assert request.ruin_threshold_type.value == ruin_type


class TestRequestLimits:
    """Tests for request parameter limits."""

    def test_horizon_min(self):
        """Verify minimum horizon is enforced."""
        with pytest.raises(ValueError):
            SimulationRequest(horizon_years=0)

    def test_horizon_max(self):
        """Verify maximum horizon is enforced."""
        with pytest.raises(ValueError):
            SimulationRequest(horizon_years=31)

    def test_horizon_at_limits(self):
        """Verify horizon at limits is valid."""
        request_min = SimulationRequest(horizon_years=1)
        assert request_min.horizon_years == 1

        request_max = SimulationRequest(horizon_years=30)
        assert request_max.horizon_years == 30

    def test_num_paths_min(self):
        """Verify minimum paths is enforced."""
        with pytest.raises(ValueError):
            SimulationRequest(num_paths=50)

    def test_num_paths_max(self):
        """Verify maximum paths is enforced."""
        with pytest.raises(ValueError):
            SimulationRequest(num_paths=10001)

    def test_num_paths_at_limits(self):
        """Verify paths at limits is valid."""
        request_min = SimulationRequest(num_paths=100)
        assert request_min.num_paths == 100

        request_max = SimulationRequest(num_paths=10000)
        assert request_max.num_paths == 10000

    def test_sample_paths_min(self):
        """Verify minimum sample paths is enforced."""
        with pytest.raises(ValueError):
            SimulationRequest(sample_paths_count=0)

    def test_sample_paths_max(self):
        """Verify maximum sample paths is enforced."""
        with pytest.raises(ValueError):
            SimulationRequest(sample_paths_count=51)


class TestResponseSchema:
    """Tests for response schema structure."""

    def test_metrics_summary_has_all_fields(self):
        """Verify MetricsSummaryResponse has all required fields."""
        metrics = MetricsSummaryResponse(
            terminal_wealth_mean=150000.0,
            terminal_wealth_median=140000.0,
            terminal_wealth_percentiles={5: 80000, 25: 110000, 75: 170000, 95: 220000},
            max_drawdown_mean=0.15,
            max_drawdown_percentiles={5: 0.05, 25: 0.10, 75: 0.20, 95: 0.35},
            cvar_95=75000.0,
            probability_of_ruin=0.05,
            ruin_threshold=0.30,
            ruin_threshold_type="percentage",
        )

        assert metrics.terminal_wealth_mean == 150000.0
        assert metrics.terminal_wealth_median == 140000.0
        assert len(metrics.terminal_wealth_percentiles) == 4
        assert metrics.max_drawdown_mean == 0.15
        assert metrics.cvar_95 == 75000.0
        assert metrics.probability_of_ruin == 0.05

    def test_sample_path_structure(self):
        """Verify SamplePathResponse structure."""
        path = SamplePathResponse(
            percentile=50,
            values=[100000.0, 105000.0, 110000.0, 115000.0],
            terminal_value=115000.0,
        )

        assert path.percentile == 50
        assert len(path.values) == 4
        assert path.terminal_value == 115000.0

    def test_simulation_response_structure(self):
        """Verify SimulationResponse combines metrics and paths with persistence fields."""
        response = SimulationResponse(
            id=uuid4(),
            portfolio_id=uuid4(),
            name="Test Simulation",
            horizon_years=5,
            num_paths=1000,
            model_type=ModelType.GAUSSIAN,
            scenario=None,
            rebalance_frequency=None,
            mu_type=MuType.HISTORICAL,
            sample_paths_count=10,
            ruin_threshold=0.30,
            ruin_threshold_type=RuinThresholdType.PERCENTAGE,
            metrics=MetricsSummaryResponse(
                terminal_wealth_mean=150000.0,
                terminal_wealth_median=140000.0,
                terminal_wealth_percentiles={5: 80000},
                max_drawdown_mean=0.15,
                max_drawdown_percentiles={5: 0.05},
                cvar_95=75000.0,
                probability_of_ruin=0.05,
                ruin_threshold=0.30,
                ruin_threshold_type="percentage",
            ),
            sample_paths=[
                SamplePathResponse(
                    percentile=50,
                    values=[100000.0, 115000.0],
                    terminal_value=115000.0,
                )
            ],
            created_at=datetime.now(timezone.utc),
        )

        assert response.id is not None
        assert response.metrics is not None
        assert len(response.sample_paths) == 1

    def test_simulation_summary_response_structure(self):
        """Verify SimulationSummaryResponse has no sample_paths."""
        summary = SimulationSummaryResponse(
            id=uuid4(),
            portfolio_id=uuid4(),
            name="Test Simulation",
            horizon_years=5,
            num_paths=1000,
            model_type=ModelType.GAUSSIAN,
            scenario=None,
            mu_type=MuType.HISTORICAL,
            metrics=MetricsSummaryResponse(
                terminal_wealth_mean=150000.0,
                terminal_wealth_median=140000.0,
                terminal_wealth_percentiles={5: 80000},
                max_drawdown_mean=0.15,
                max_drawdown_percentiles={5: 0.05},
                cvar_95=75000.0,
                probability_of_ruin=0.05,
                ruin_threshold=0.30,
                ruin_threshold_type="percentage",
            ),
            created_at=datetime.now(timezone.utc),
        )

        assert summary.id is not None
        assert summary.metrics is not None
        # Summary should not have sample_paths
        assert not hasattr(summary, "sample_paths") or "sample_paths" not in summary.model_fields


class TestRuinThresholdTypes:
    """Tests for ruin threshold configuration."""

    def test_percentage_threshold(self):
        """Verify percentage threshold works."""
        request = SimulationRequest(
            ruin_threshold=0.30,
            ruin_threshold_type=RuinThresholdType.PERCENTAGE,
        )
        assert request.ruin_threshold == 0.30
        assert request.ruin_threshold_type == RuinThresholdType.PERCENTAGE

    def test_absolute_threshold(self):
        """Verify absolute threshold works."""
        request = SimulationRequest(
            ruin_threshold=70000.0,
            ruin_threshold_type=RuinThresholdType.ABSOLUTE,
        )
        assert request.ruin_threshold == 70000.0
        assert request.ruin_threshold_type == RuinThresholdType.ABSOLUTE

    def test_no_threshold(self):
        """Verify no threshold is valid."""
        request = SimulationRequest(ruin_threshold=None)
        assert request.ruin_threshold is None


class TestEdgeCases:
    """Tests for edge cases in request/response handling."""

    def test_minimal_request(self):
        """Verify minimal request with just required validation."""
        request = SimulationRequest()
        # Should have sensible defaults
        assert request.num_paths >= 100

    def test_zero_ruin_threshold(self):
        """Verify zero ruin threshold is valid."""
        request = SimulationRequest(ruin_threshold=0.0)
        assert request.ruin_threshold == 0.0

    def test_high_ruin_threshold_percentage(self):
        """Verify high percentage threshold is valid (90% loss)."""
        request = SimulationRequest(
            ruin_threshold=0.90,
            ruin_threshold_type=RuinThresholdType.PERCENTAGE,
        )
        assert request.ruin_threshold == 0.90

    def test_sample_paths_equals_one(self):
        """Verify single sample path request is valid."""
        request = SimulationRequest(sample_paths_count=1)
        assert request.sample_paths_count == 1

    def test_all_model_types_valid(self):
        """Verify all model types can be specified."""
        for model_type in ModelType:
            request = SimulationRequest(model_type=model_type)
            assert request.model_type == model_type

    def test_all_scenario_types_valid(self):
        """Verify all scenario types can be specified."""
        for scenario in ScenarioType:
            request = SimulationRequest(scenario=scenario)
            assert request.scenario == scenario
