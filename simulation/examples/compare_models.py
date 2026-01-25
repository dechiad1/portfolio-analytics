#!/usr/bin/env python3
"""
Example script comparing different return models and scenarios.

This script demonstrates the simulation engine with a 3-asset portfolio,
comparing Gaussian, Student-t, and Regime-switching models with and
without stress scenarios.

Run from simulation directory:
    poetry run python examples/compare_models.py
"""

import numpy as np

from simulation import (
    Simulator,
    SimulationRequest,
    SimulationParams,
    ModelType,
    ScenarioType,
    RebalanceFrequency,
    RuinThresholdType,
)


def create_sample_portfolio() -> SimulationParams:
    """Create a sample 3-asset portfolio for demonstration."""
    return SimulationParams(
        tickers=("SPY", "BND", "GLD"),
        weights=np.array([0.60, 0.30, 0.10]),  # 60/30/10 allocation
        mu=np.array([0.10, 0.04, 0.05]),  # Expected annual returns
        volatility=np.array([0.18, 0.05, 0.15]),  # Annual volatility
        correlation_matrix=np.array([
            [1.00, 0.20, 0.00],  # SPY
            [0.20, 1.00, 0.10],  # BND
            [0.00, 0.10, 1.00],  # GLD
        ]),
        initial_portfolio_value=100000.0,
    )


def print_metrics(name: str, result) -> None:
    """Print key metrics from simulation result."""
    m = result.metrics
    print(f"\n{'='*60}")
    print(f"  {name}")
    print(f"{'='*60}")
    print(f"  Terminal Wealth:")
    print(f"    Mean:   ${m.terminal_wealth_mean:>12,.0f}")
    print(f"    Median: ${m.terminal_wealth_median:>12,.0f}")
    print(f"    5th %:  ${m.terminal_wealth_percentiles[5]:>12,.0f}")
    print(f"    95th %: ${m.terminal_wealth_percentiles[95]:>12,.0f}")
    print(f"  Risk Metrics:")
    print(f"    Max Drawdown (mean): {m.max_drawdown_mean*100:>6.1f}%")
    print(f"    CVaR 95%:            ${m.cvar_95:>12,.0f}")
    print(f"    Prob of Ruin (30%):  {m.probability_of_ruin*100:>6.1f}%")


def main() -> None:
    """Run comparison of models and scenarios."""
    print("\n" + "="*70)
    print("  PORTFOLIO SIMULATION: MODEL & SCENARIO COMPARISON")
    print("="*70)

    # Create portfolio and simulator
    params = create_sample_portfolio()
    simulator = Simulator(steps_per_year=4)  # Quarterly steps

    print("\nPortfolio Configuration:")
    print(f"  Assets: {', '.join(params.tickers)}")
    print(f"  Weights: {params.weights}")
    print(f"  Initial Value: ${params.initial_portfolio_value:,.0f}")
    print(f"  Simulation: 5 years (20 quarterly steps), 1000 paths")

    # Base request configuration
    base_config = {
        "params": params,
        "steps": 20,  # 5 years * 4 quarters
        "num_paths": 1000,
        "sample_paths_count": 5,
        "ruin_threshold": 0.30,  # 30% loss
        "ruin_threshold_type": RuinThresholdType.PERCENTAGE,
        "seed": 42,  # For reproducibility
    }

    # 1. Compare Models (no scenario)
    print("\n" + "-"*70)
    print("  PART 1: MODEL COMPARISON (No Scenario)")
    print("-"*70)

    for model_type in [ModelType.GAUSSIAN, ModelType.STUDENT_T, ModelType.REGIME_SWITCHING]:
        request = SimulationRequest(
            **base_config,
            model_type=model_type,
        )
        result = simulator.run(request)
        print_metrics(f"{model_type.value.upper()} Model", result)

    # 2. Compare Scenarios (with Gaussian model)
    print("\n" + "-"*70)
    print("  PART 2: SCENARIO COMPARISON (Gaussian Model)")
    print("-"*70)

    scenarios = [None, ScenarioType.JAPAN_LOST_DECADE, ScenarioType.STAGFLATION]
    scenario_names = ["No Scenario (Baseline)", "Japan Lost Decade", "Stagflation"]

    for scenario, name in zip(scenarios, scenario_names):
        request = SimulationRequest(
            **base_config,
            model_type=ModelType.GAUSSIAN,
            scenario=scenario,
        )
        result = simulator.run(request)
        print_metrics(name, result)

    # 3. Impact of Rebalancing
    print("\n" + "-"*70)
    print("  PART 3: REBALANCING IMPACT (Gaussian Model)")
    print("-"*70)

    for rebalance in [None, RebalanceFrequency.QUARTERLY]:
        rebalance_name = "No Rebalancing" if rebalance is None else "Quarterly Rebalancing"
        request = SimulationRequest(
            **base_config,
            model_type=ModelType.GAUSSIAN,
            rebalance_frequency=rebalance,
            rebalance_threshold=0.05,
            transaction_cost_bps=10.0,
        )
        result = simulator.run(request)
        print_metrics(rebalance_name, result)

    # 4. Sample Paths Display
    print("\n" + "-"*70)
    print("  PART 4: SAMPLE PATHS (Gaussian, 5-year horizon)")
    print("-"*70)

    request = SimulationRequest(
        **base_config,
        model_type=ModelType.GAUSSIAN,
    )
    result = simulator.run(request)

    print("\n  Representative paths by percentile:")
    print("  " + "-"*56)
    print(f"  {'Percentile':>10} | {'Start':>12} | {'Terminal':>12} | {'Return':>10}")
    print("  " + "-"*56)
    for path in result.sample_paths:
        start = path.values[0]
        end = path.terminal_value
        ret = (end / start - 1) * 100
        print(f"  {path.percentile:>10}th | ${start:>10,.0f} | ${end:>10,.0f} | {ret:>+9.1f}%")

    print("\n" + "="*70)
    print("  SIMULATION COMPLETE")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
