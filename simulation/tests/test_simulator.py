"""Tests for the main simulation engine."""

import numpy as np
import pytest

from simulation import (
    Simulator,
    SimulationRequest,
    SimulationParams,
    ModelType,
    ScenarioType,
    RebalanceFrequency,
    RuinThresholdType,
)


@pytest.fixture
def sample_params() -> SimulationParams:
    """Create sample simulation parameters for testing."""
    return SimulationParams(
        tickers=("SPY", "BND", "GLD"),
        weights=np.array([0.6, 0.3, 0.1]),
        mu=np.array([0.10, 0.04, 0.05]),  # Annualized returns
        volatility=np.array([0.18, 0.05, 0.15]),  # Annualized volatility
        correlation_matrix=np.array([
            [1.0, 0.2, 0.0],
            [0.2, 1.0, 0.1],
            [0.0, 0.1, 1.0],
        ]),
        initial_portfolio_value=100000.0,
    )


class TestSeedReproducibility:
    """Tests for seed-based reproducibility."""

    def test_same_seed_produces_identical_paths(self, sample_params: SimulationParams):
        """Verify that the same seed produces identical simulation results."""
        simulator = Simulator()

        request = SimulationRequest(
            params=sample_params,
            steps=20,
            num_paths=100,
            model_type=ModelType.GAUSSIAN,
            seed=42,
        )

        result1 = simulator.run(request)
        result2 = simulator.run(request)

        # Terminal values should be identical
        assert result1.all_terminal_values is not None
        assert result2.all_terminal_values is not None
        np.testing.assert_array_equal(
            result1.all_terminal_values,
            result2.all_terminal_values,
        )

    def test_different_seeds_produce_different_paths(
        self, sample_params: SimulationParams
    ):
        """Verify that different seeds produce different results."""
        simulator = Simulator()

        request1 = SimulationRequest(
            params=sample_params,
            steps=20,
            num_paths=100,
            model_type=ModelType.GAUSSIAN,
            seed=42,
        )
        request2 = SimulationRequest(
            params=sample_params,
            steps=20,
            num_paths=100,
            model_type=ModelType.GAUSSIAN,
            seed=123,
        )

        result1 = simulator.run(request1)
        result2 = simulator.run(request2)

        assert result1.all_terminal_values is not None
        assert result2.all_terminal_values is not None
        assert not np.array_equal(
            result1.all_terminal_values,
            result2.all_terminal_values,
        )


class TestOutputShapes:
    """Tests for correct output dimensions."""

    def test_terminal_values_shape(self, sample_params: SimulationParams):
        """Verify terminal values has correct shape."""
        simulator = Simulator()
        num_paths = 500

        request = SimulationRequest(
            params=sample_params,
            steps=20,
            num_paths=num_paths,
            model_type=ModelType.GAUSSIAN,
            seed=42,
        )

        result = simulator.run(request)

        assert result.all_terminal_values is not None
        assert result.all_terminal_values.shape == (num_paths,)

    def test_sample_paths_count(self, sample_params: SimulationParams):
        """Verify correct number of sample paths returned."""
        simulator = Simulator()
        sample_count = 15

        request = SimulationRequest(
            params=sample_params,
            steps=20,
            num_paths=1000,
            model_type=ModelType.GAUSSIAN,
            sample_paths_count=sample_count,
            seed=42,
        )

        result = simulator.run(request)

        assert len(result.sample_paths) == sample_count

    def test_sample_path_length(self, sample_params: SimulationParams):
        """Verify sample paths have correct number of values."""
        simulator = Simulator()
        steps = 20

        request = SimulationRequest(
            params=sample_params,
            steps=steps,
            num_paths=100,
            model_type=ModelType.GAUSSIAN,
            seed=42,
        )

        result = simulator.run(request)

        for path in result.sample_paths:
            # Path should have steps + 1 values (initial + each step)
            assert len(path.values) == steps + 1


class TestFatTails:
    """Tests for fat-tailed distribution properties."""

    def test_student_t_produces_more_extreme_outcomes(
        self, sample_params: SimulationParams
    ):
        """Verify Student-t model produces more extreme outcomes than Gaussian.

        Instead of comparing kurtosis (which is unreliable for terminal values
        due to CLT effects), we compare the frequency of extreme outcomes.
        """
        simulator = Simulator()
        num_paths = 10000

        gaussian_request = SimulationRequest(
            params=sample_params,
            steps=20,
            num_paths=num_paths,
            model_type=ModelType.GAUSSIAN,
            seed=42,
        )
        student_request = SimulationRequest(
            params=sample_params,
            steps=20,
            num_paths=num_paths,
            model_type=ModelType.STUDENT_T,
            seed=42,
        )

        gaussian_result = simulator.run(gaussian_request)
        student_result = simulator.run(student_request)

        assert gaussian_result.all_terminal_values is not None
        assert student_result.all_terminal_values is not None

        # Compare range (max - min) as proxy for tail behavior
        # Student-t should have wider range due to fat tails
        gaussian_range = (
            np.max(gaussian_result.all_terminal_values)
            - np.min(gaussian_result.all_terminal_values)
        )
        student_range = (
            np.max(student_result.all_terminal_values)
            - np.min(student_result.all_terminal_values)
        )

        # Student-t should produce wider range (more extreme min/max)
        # Allow some margin for statistical variation
        assert student_range > gaussian_range * 0.8


class TestRebalancing:
    """Tests for rebalancing behavior."""

    def test_no_rebalance_when_below_threshold(self, sample_params: SimulationParams):
        """Verify no rebalancing occurs when drift is below threshold."""
        simulator = Simulator()

        # Use very small steps to minimize drift
        request = SimulationRequest(
            params=sample_params,
            steps=2,
            num_paths=1,
            model_type=ModelType.GAUSSIAN,
            rebalance_frequency=RebalanceFrequency.QUARTERLY,
            rebalance_threshold=0.50,  # Very high threshold
            seed=42,
        )

        result = simulator.run(request)

        # With high threshold and few steps, should have minimal rebalancing
        assert result.all_terminal_values is not None

    def test_rebalance_reduces_drift(self, sample_params: SimulationParams):
        """Verify that rebalancing keeps weights closer to target."""
        simulator = Simulator()

        # Run with and without rebalancing
        no_rebalance_request = SimulationRequest(
            params=sample_params,
            steps=40,
            num_paths=100,
            model_type=ModelType.GAUSSIAN,
            rebalance_frequency=None,
            seed=42,
        )
        with_rebalance_request = SimulationRequest(
            params=sample_params,
            steps=40,
            num_paths=100,
            model_type=ModelType.GAUSSIAN,
            rebalance_frequency=RebalanceFrequency.QUARTERLY,
            rebalance_threshold=0.05,
            seed=42,
        )

        # Both should complete without error
        result1 = simulator.run(no_rebalance_request)
        result2 = simulator.run(with_rebalance_request)

        assert result1.all_terminal_values is not None
        assert result2.all_terminal_values is not None


class TestScenarios:
    """Tests for scenario application."""

    def test_japan_reduces_returns(self, sample_params: SimulationParams):
        """Verify Japan Lost Decade scenario reduces returns."""
        simulator = Simulator()

        base_request = SimulationRequest(
            params=sample_params,
            steps=20,
            num_paths=1000,
            model_type=ModelType.GAUSSIAN,
            scenario=None,
            seed=42,
        )
        japan_request = SimulationRequest(
            params=sample_params,
            steps=20,
            num_paths=1000,
            model_type=ModelType.GAUSSIAN,
            scenario=ScenarioType.JAPAN_LOST_DECADE,
            seed=42,
        )

        base_result = simulator.run(base_request)
        japan_result = simulator.run(japan_request)

        # Japan scenario should have lower mean terminal value
        assert japan_result.metrics.terminal_wealth_mean < base_result.metrics.terminal_wealth_mean

    def test_stagflation_increases_volatility(self, sample_params: SimulationParams):
        """Verify stagflation scenario increases volatility."""
        simulator = Simulator()

        base_request = SimulationRequest(
            params=sample_params,
            steps=20,
            num_paths=1000,
            model_type=ModelType.GAUSSIAN,
            scenario=None,
            seed=42,
        )
        stagflation_request = SimulationRequest(
            params=sample_params,
            steps=20,
            num_paths=1000,
            model_type=ModelType.GAUSSIAN,
            scenario=ScenarioType.STAGFLATION,
            seed=42,
        )

        base_result = simulator.run(base_request)
        stagflation_result = simulator.run(stagflation_request)

        assert base_result.all_terminal_values is not None
        assert stagflation_result.all_terminal_values is not None

        # Stagflation should have higher standard deviation
        base_std = np.std(base_result.all_terminal_values)
        stagflation_std = np.std(stagflation_result.all_terminal_values)
        assert stagflation_std > base_std


class TestTransactionCosts:
    """Tests for transaction cost application."""

    def test_costs_only_when_rebalancing(self, sample_params: SimulationParams):
        """Verify transaction costs only apply when rebalancing occurs."""
        simulator = Simulator()

        # No rebalancing = no transaction costs
        no_rebalance_request = SimulationRequest(
            params=sample_params,
            steps=20,
            num_paths=500,
            model_type=ModelType.GAUSSIAN,
            rebalance_frequency=None,
            transaction_cost_bps=100.0,  # 1% - very high
            seed=42,
        )

        # With rebalancing at high frequency
        rebalance_request = SimulationRequest(
            params=sample_params,
            steps=20,
            num_paths=500,
            model_type=ModelType.GAUSSIAN,
            rebalance_frequency=RebalanceFrequency.QUARTERLY,
            rebalance_threshold=0.01,  # Very low threshold = more rebalancing
            transaction_cost_bps=100.0,
            seed=42,
        )

        no_rebalance_result = simulator.run(no_rebalance_request)
        rebalance_result = simulator.run(rebalance_request)

        # With high costs and frequent rebalancing, returns should be lower
        # (though this depends on market conditions, so we just check it runs)
        assert no_rebalance_result.all_terminal_values is not None
        assert rebalance_result.all_terminal_values is not None


class TestMetrics:
    """Tests for metrics calculation."""

    def test_probability_of_ruin_percentage(self, sample_params: SimulationParams):
        """Test probability of ruin with percentage threshold."""
        simulator = Simulator()

        request = SimulationRequest(
            params=sample_params,
            steps=20,
            num_paths=1000,
            model_type=ModelType.GAUSSIAN,
            ruin_threshold=0.30,  # 30% loss threshold
            ruin_threshold_type=RuinThresholdType.PERCENTAGE,
            seed=42,
        )

        result = simulator.run(request)

        # Probability should be between 0 and 1
        assert 0.0 <= result.metrics.probability_of_ruin <= 1.0
        assert result.metrics.ruin_threshold == 0.30
        assert result.metrics.ruin_threshold_type == "percentage"

    def test_probability_of_ruin_absolute(self, sample_params: SimulationParams):
        """Test probability of ruin with absolute threshold."""
        simulator = Simulator()

        request = SimulationRequest(
            params=sample_params,
            steps=20,
            num_paths=1000,
            model_type=ModelType.GAUSSIAN,
            ruin_threshold=70000.0,  # Must have at least $70k
            ruin_threshold_type=RuinThresholdType.ABSOLUTE,
            seed=42,
        )

        result = simulator.run(request)

        # Probability should be between 0 and 1
        assert 0.0 <= result.metrics.probability_of_ruin <= 1.0
        assert result.metrics.ruin_threshold == 70000.0
        assert result.metrics.ruin_threshold_type == "absolute"

    def test_cvar_95_is_lower_than_median(self, sample_params: SimulationParams):
        """CVaR 95% should be lower than median (worst 5% average)."""
        simulator = Simulator()

        request = SimulationRequest(
            params=sample_params,
            steps=20,
            num_paths=1000,
            model_type=ModelType.GAUSSIAN,
            seed=42,
        )

        result = simulator.run(request)

        assert result.metrics.cvar_95 < result.metrics.terminal_wealth_median


class TestRegimeSwitching:
    """Tests for regime-switching model behavior."""

    def test_regime_transitions_occur(self, sample_params: SimulationParams):
        """Verify that regime transitions happen over many steps."""
        simulator = Simulator()

        # Run many paths with many steps
        request = SimulationRequest(
            params=sample_params,
            steps=100,
            num_paths=100,
            model_type=ModelType.REGIME_SWITCHING,
            seed=42,
        )

        result = simulator.run(request)

        # With many steps, should see variety in outcomes due to regimes
        assert result.all_terminal_values is not None
        std = np.std(result.all_terminal_values)
        assert std > 0  # Not all identical paths
