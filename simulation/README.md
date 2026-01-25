# Portfolio Simulation Engine

A portfolio stress-testing simulation engine for Monte Carlo analysis.

## Features

- Multiple return models (Gaussian, Student-t, Regime-switching)
- Stress test scenarios (Japan Lost Decade, Stagflation)
- Rebalancing with drift tolerance
- Transaction cost modeling
- Probability of ruin calculations

## Installation

```bash
cd simulation
poetry install
```

## Usage

```python
from simulation import Simulator, SimulationRequest, SimulationParams, ModelType

# Create parameters
params = SimulationParams(
    tickers=("SPY", "BND", "GLD"),
    weights=np.array([0.6, 0.3, 0.1]),
    mu=np.array([0.10, 0.04, 0.05]),
    volatility=np.array([0.18, 0.05, 0.15]),
    correlation_matrix=np.array([[1.0, 0.2, 0.0], [0.2, 1.0, 0.1], [0.0, 0.1, 1.0]]),
    initial_portfolio_value=100000.0,
)

# Run simulation
request = SimulationRequest(
    params=params,
    steps=20,  # 20 quarters = 5 years
    num_paths=1000,
    model_type=ModelType.GAUSSIAN,
)

simulator = Simulator()
result = simulator.run(request)
print(f"Mean terminal value: ${result.metrics.terminal_wealth_mean:,.2f}")
```

## Testing

```bash
cd simulation
pytest
```
