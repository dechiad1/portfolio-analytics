"""Service for running portfolio simulations."""

from decimal import Decimal
from uuid import UUID

import numpy as np

from domain.models.position import Position
from domain.ports.position_repository import PositionRepository
from domain.ports.portfolio_repository import PortfolioRepository
from domain.ports.simulation_params_repository import SimulationParamsRepository


class SimulationError(Exception):
    """Base exception for simulation errors."""

    pass


class InsufficientDataError(SimulationError):
    """Raised when there isn't enough data to run simulation."""

    pass


class SimulationService:
    """Service for running portfolio stress-test simulations."""

    STEPS_PER_YEAR = 4  # Quarterly

    def __init__(
        self,
        portfolio_repository: PortfolioRepository,
        position_repository: PositionRepository,
        simulation_params_repository: SimulationParamsRepository,
    ) -> None:
        self._portfolio_repo = portfolio_repository
        self._position_repo = position_repository
        self._sim_params_repo = simulation_params_repository

    def run_simulation(
        self,
        portfolio_id: UUID,
        user_id: UUID,
        horizon_years: int,
        num_paths: int,
        model_type: str,
        scenario: str | None,
        rebalance_frequency: str | None,
        mu_type: str,
        sample_paths_count: int,
        ruin_threshold: float | None,
        ruin_threshold_type: str,
        is_admin: bool = False,
    ) -> dict:
        """Run simulation for a portfolio.

        Args:
            portfolio_id: Portfolio to simulate
            user_id: Requesting user's ID
            horizon_years: Number of years to simulate
            num_paths: Number of Monte Carlo paths
            model_type: Return model type
            scenario: Stress test scenario
            rebalance_frequency: Rebalancing frequency
            mu_type: Source for expected returns (historical/forward)
            sample_paths_count: Number of representative paths to return
            ruin_threshold: Threshold for probability of ruin
            ruin_threshold_type: Whether threshold is percentage or absolute
            is_admin: Whether requesting user is admin

        Returns:
            Simulation results dictionary
        """
        # Import simulation package
        from simulation import (
            Simulator,
            SimulationRequest as SimRequest,
            SimulationParams,
            ModelType,
            MuType,
            ScenarioType,
            RebalanceFrequency,
            RuinThresholdType,
        )

        # Verify portfolio access
        portfolio = self._portfolio_repo.get_by_id(portfolio_id)
        if portfolio is None:
            raise SimulationError(f"Portfolio {portfolio_id} not found")
        if not is_admin and portfolio.user_id != user_id:
            raise SimulationError("Access denied to this portfolio")

        # Get portfolio positions
        positions = self._position_repo.get_by_portfolio_id(portfolio_id)
        if not positions:
            raise SimulationError("Portfolio has no positions")
        tickers, weights, initial_value = self._calculate_weights_from_positions(
            positions
        )
        if not tickers:
            raise SimulationError("No valid holdings with market value")

        # Fetch simulation parameters from data warehouse
        security_params = self._sim_params_repo.get_security_params(tickers)
        historical_returns = self._sim_params_repo.get_historical_returns(tickers)

        # Build mu and volatility arrays
        mu, volatility = self._build_param_arrays(
            tickers, security_params, mu_type
        )

        # Build correlation matrix from historical returns
        correlation_matrix = self._build_correlation_matrix(
            tickers, historical_returns
        )

        # Create simulation parameters
        params = SimulationParams(
            tickers=tuple(tickers),
            weights=weights,
            mu=mu,
            volatility=volatility,
            correlation_matrix=correlation_matrix,
            initial_portfolio_value=initial_value,
        )

        # Convert API enums to simulation enums
        sim_model_type = ModelType(model_type)
        sim_scenario = ScenarioType(scenario) if scenario else None
        sim_rebalance = RebalanceFrequency(rebalance_frequency) if rebalance_frequency else None
        sim_mu_type = MuType(mu_type)
        sim_ruin_type = RuinThresholdType(ruin_threshold_type)

        # Create simulation request
        steps = horizon_years * self.STEPS_PER_YEAR
        request = SimRequest(
            params=params,
            steps=steps,
            num_paths=num_paths,
            model_type=sim_model_type,
            scenario=sim_scenario,
            rebalance_frequency=sim_rebalance,
            sample_paths_count=sample_paths_count,
            ruin_threshold=ruin_threshold,
            ruin_threshold_type=sim_ruin_type,
        )

        # Run simulation
        simulator = Simulator(steps_per_year=self.STEPS_PER_YEAR)
        result = simulator.run(request)

        # Convert to response format
        return {
            "metrics": {
                "terminal_wealth_mean": result.metrics.terminal_wealth_mean,
                "terminal_wealth_median": result.metrics.terminal_wealth_median,
                "terminal_wealth_percentiles": result.metrics.terminal_wealth_percentiles,
                "max_drawdown_mean": result.metrics.max_drawdown_mean,
                "max_drawdown_percentiles": result.metrics.max_drawdown_percentiles,
                "cvar_95": result.metrics.cvar_95,
                "probability_of_ruin": result.metrics.probability_of_ruin,
                "ruin_threshold": result.metrics.ruin_threshold,
                "ruin_threshold_type": result.metrics.ruin_threshold_type,
            },
            "sample_paths": [
                {
                    "percentile": path.percentile,
                    "values": list(path.values),
                    "terminal_value": path.terminal_value,
                }
                for path in result.sample_paths
            ],
        }

    def _calculate_weights_from_positions(
        self, positions: list[Position]
    ) -> tuple[list[str], np.ndarray, float]:
        """Calculate portfolio weights from positions.

        Uses market_value if current_price is available, otherwise cost_basis.

        Returns:
            Tuple of (tickers, weights array, total portfolio value)
        """
        tickers = []
        values = []

        for p in positions:
            ticker = p.ticker
            if not ticker:
                continue

            # Use market_value if available, else cost_basis
            value = p.market_value if p.market_value else p.cost_basis
            if value and value > Decimal("0"):
                tickers.append(ticker)
                values.append(float(value))

        if not tickers:
            return [], np.array([]), 0.0

        values_arr = np.array(values, dtype=np.float64)
        total_value = float(values_arr.sum())
        weights = values_arr / total_value

        return tickers, weights, total_value

    def _build_param_arrays(
        self,
        tickers: list[str],
        security_params: list,
        mu_type: str,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Build mu and volatility arrays from security params.

        Uses default values for missing data.
        """
        params_by_ticker = {sp.ticker: sp for sp in security_params}

        mu_list = []
        vol_list = []

        for ticker in tickers:
            sp = params_by_ticker.get(ticker)
            if sp is None:
                # Default values for missing securities
                mu_list.append(0.05)  # 5% default return
                vol_list.append(0.20)  # 20% default volatility
            else:
                # Get mu based on preference
                if mu_type == "forward" and sp.forward_mu is not None:
                    mu_list.append(sp.forward_mu)
                elif sp.historical_mu is not None:
                    mu_list.append(sp.historical_mu)
                else:
                    mu_list.append(0.05)

                # Get volatility
                if sp.volatility is not None:
                    vol_list.append(sp.volatility)
                else:
                    vol_list.append(0.20)

        return (
            np.array(mu_list, dtype=np.float64),
            np.array(vol_list, dtype=np.float64),
        )

    def _build_correlation_matrix(
        self,
        tickers: list[str],
        historical_returns: dict[str, np.ndarray],
    ) -> np.ndarray:
        """Build correlation matrix from historical returns.

        Uses identity matrix with small correlations for missing data.
        """
        n = len(tickers)
        if n == 1:
            return np.array([[1.0]], dtype=np.float64)

        # Find common dates by aligning returns
        # For simplicity, use available data and assume alignment
        # In production, would properly align by date

        # Build return matrix
        returns_matrix = []
        for ticker in tickers:
            if ticker in historical_returns and len(historical_returns[ticker]) > 0:
                returns_matrix.append(historical_returns[ticker])
            else:
                # Create synthetic returns if missing
                returns_matrix.append(np.random.randn(252) * 0.01)

        # Align lengths (use shortest)
        min_len = min(len(r) for r in returns_matrix)
        if min_len < 30:
            # Not enough data for correlation, use default
            return self._default_correlation_matrix(n)

        aligned_returns = np.array(
            [r[:min_len] for r in returns_matrix], dtype=np.float64
        )

        # Calculate correlation matrix
        corr_matrix = np.corrcoef(aligned_returns)

        # Ensure positive definiteness
        corr_matrix = self._ensure_positive_definite(corr_matrix)

        return corr_matrix

    def _default_correlation_matrix(self, n: int) -> np.ndarray:
        """Create default correlation matrix with small off-diagonal values."""
        corr = np.eye(n, dtype=np.float64)
        # Add small positive correlation between assets
        for i in range(n):
            for j in range(n):
                if i != j:
                    corr[i, j] = 0.2  # Default 0.2 correlation
        return corr

    def _ensure_positive_definite(
        self, matrix: np.ndarray
    ) -> np.ndarray:
        """Ensure matrix is positive definite."""
        # Fix any NaN values
        matrix = np.nan_to_num(matrix, nan=0.0)

        # Ensure diagonal is 1
        np.fill_diagonal(matrix, 1.0)

        # Check positive definiteness
        eigvals = np.linalg.eigvalsh(matrix)
        if np.min(eigvals) <= 0:
            # Add small value to diagonal
            matrix = matrix + np.eye(len(matrix)) * (abs(np.min(eigvals)) + 0.01)
            # Re-normalize to have 1s on diagonal
            d = np.sqrt(np.diag(matrix))
            matrix = matrix / np.outer(d, d)

        return matrix
