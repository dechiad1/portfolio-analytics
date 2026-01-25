"""Main simulation runner."""

import numpy as np
from numpy.random import default_rng, Generator
from numpy.typing import NDArray

from simulation.types import (
    ModelType,
    ScenarioType,
    Regime,
    SimulationRequest,
    SimulationResult,
    SimulationParams,
    State,
)
from simulation.models import (
    GaussianMVNModel,
    StudentTMVNModel,
    RegimeSwitchingModel,
)
from simulation.scenarios import (
    JapanLostDecadeScenario,
    StagflationScenario,
)
from simulation.engine.rebalancer import Rebalancer
from simulation.engine.frictions import TransactionCosts
from simulation.results.metrics import compute_metrics
from simulation.results.paths import select_representative_paths


class Simulator:
    """Main simulation engine.

    Runs Monte Carlo simulations of portfolio returns with:
    - Multiple return model options
    - Stress test scenarios
    - Rebalancing with drift tolerance
    - Transaction costs
    """

    def __init__(self, steps_per_year: int = 4) -> None:
        """Initialize simulator.

        Args:
            steps_per_year: Number of simulation steps per year (4 = quarterly)
        """
        self._steps_per_year = steps_per_year

    def _create_model(self, model_type: ModelType):
        """Create return model based on type."""
        if model_type == ModelType.GAUSSIAN:
            return GaussianMVNModel(steps_per_year=self._steps_per_year)
        elif model_type == ModelType.STUDENT_T:
            return StudentTMVNModel(
                degrees_of_freedom=5.0,
                steps_per_year=self._steps_per_year,
            )
        elif model_type == ModelType.REGIME_SWITCHING:
            return RegimeSwitchingModel(steps_per_year=self._steps_per_year)
        else:
            raise ValueError(f"Unknown model type: {model_type}")

    def _create_scenario(self, scenario_type: ScenarioType | None):
        """Create scenario based on type."""
        if scenario_type is None:
            return None
        elif scenario_type == ScenarioType.JAPAN_LOST_DECADE:
            return JapanLostDecadeScenario()
        elif scenario_type == ScenarioType.STAGFLATION:
            return StagflationScenario()
        else:
            raise ValueError(f"Unknown scenario type: {scenario_type}")

    def _run_single_path(
        self,
        request: SimulationRequest,
        model,
        scenario,
        rebalancer: Rebalancer,
        transaction_costs: TransactionCosts,
        rng: Generator,
    ) -> tuple[NDArray[np.floating], float, float]:
        """Run a single simulation path.

        Returns:
            Tuple of (path_values, terminal_value, max_drawdown)
        """
        params = request.params

        # Initialize state
        state = State(
            current_weights=params.weights.copy(),
            portfolio_value=params.initial_portfolio_value,
            current_regime=Regime.CALM,
            step=0,
        )

        # Track path values for metrics
        path_values = [state.portfolio_value]
        peak_value = state.portfolio_value
        max_drawdown = 0.0

        for t in range(request.steps):
            # Apply scenario modifications if active
            step_params = params
            if scenario is not None:
                step_params = scenario.apply(params, state, t)

            # Sample returns
            returns = model.sample_returns(state, step_params, t, rng)

            # Apply any scenario shocks
            if scenario is not None:
                shock = scenario.apply_shock(state, t)
                if shock is not None:
                    returns = returns + shock

            # Update state based on model type
            if isinstance(model, RegimeSwitchingModel):
                state = model.update_state(state, returns, rng)
            else:
                state = model.update_state(state, returns)

            # Check for rebalancing
            if request.rebalance_frequency is not None:
                if rebalancer.needs_rebalance(state.current_weights, params.weights):
                    new_weights, turnover = rebalancer.rebalance(state, params)
                    cost = transaction_costs.calculate_cost(
                        state.portfolio_value, turnover
                    )
                    state = State(
                        current_weights=new_weights,
                        portfolio_value=state.portfolio_value - cost,
                        current_regime=state.current_regime,
                        step=state.step,
                    )

            # Track metrics
            path_values.append(state.portfolio_value)
            peak_value = max(peak_value, state.portfolio_value)
            if peak_value > 0:
                current_drawdown = (peak_value - state.portfolio_value) / peak_value
                max_drawdown = max(max_drawdown, current_drawdown)

        return (
            np.array(path_values, dtype=np.float64),
            state.portfolio_value,
            max_drawdown,
        )

    def run(self, request: SimulationRequest) -> SimulationResult:
        """Run Monte Carlo simulation.

        Args:
            request: Simulation request with parameters and configuration

        Returns:
            SimulationResult with metrics and sample paths
        """
        # Create RNG for reproducibility
        rng = default_rng(request.seed)

        # Create model and scenario
        model = self._create_model(request.model_type)
        scenario = self._create_scenario(request.scenario)

        # Create rebalancer and transaction costs
        rebalancer = Rebalancer(
            threshold=request.rebalance_threshold,
            target_weights=request.params.weights,
        )
        transaction_costs = TransactionCosts(cost_bps=request.transaction_cost_bps)

        # Run all paths
        all_paths: list[NDArray[np.floating]] = []
        terminal_values: list[float] = []
        max_drawdowns: list[float] = []

        for _ in range(request.num_paths):
            path, terminal, max_dd = self._run_single_path(
                request=request,
                model=model,
                scenario=scenario,
                rebalancer=rebalancer,
                transaction_costs=transaction_costs,
                rng=rng,
            )
            all_paths.append(path)
            terminal_values.append(terminal)
            max_drawdowns.append(max_dd)

        # Compute metrics
        terminal_values_arr = np.array(terminal_values, dtype=np.float64)
        max_drawdowns_arr = np.array(max_drawdowns, dtype=np.float64)

        metrics = compute_metrics(
            terminal_values=terminal_values_arr,
            max_drawdowns=max_drawdowns_arr,
            initial_value=request.params.initial_portfolio_value,
            ruin_threshold=request.ruin_threshold,
            ruin_threshold_type=request.ruin_threshold_type,
        )

        # Select representative paths
        sample_paths = select_representative_paths(
            paths=all_paths,
            terminal_values=terminal_values_arr,
            count=request.sample_paths_count,
        )

        return SimulationResult(
            metrics=metrics,
            sample_paths=sample_paths,
            all_terminal_values=terminal_values_arr,
        )
