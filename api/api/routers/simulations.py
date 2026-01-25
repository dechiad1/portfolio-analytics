"""Router for portfolio simulation endpoints."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from api.routers.auth import get_current_user_full
from api.schemas.simulation import (
    SimulationRequest,
    SimulationResponse,
    SimulationSummaryResponse,
    SimulationRenameRequest,
    MetricsSummaryResponse,
    SamplePathResponse,
    ModelType,
    MuType,
    ScenarioType,
    RebalanceFrequency,
    RuinThresholdType,
)
from dependencies import (
    get_simulation_service,
    get_simulation_repository,
    get_portfolio_repository,
)
from domain.models.user import User
from domain.models.simulation import Simulation
from domain.services.simulation_service import SimulationService, SimulationError
from domain.ports.simulation_repository import SimulationRepository
from domain.ports.portfolio_repository import PortfolioRepository

router = APIRouter(tags=["simulations"])

# Thread pool for CPU-bound simulation work
_executor = ThreadPoolExecutor(max_workers=2)


def _simulation_to_response(sim: Simulation) -> SimulationResponse:
    """Convert a Simulation model to a SimulationResponse."""
    return SimulationResponse(
        id=sim.id,
        portfolio_id=sim.portfolio_id,
        name=sim.name,
        horizon_years=sim.horizon_years,
        num_paths=sim.num_paths,
        model_type=ModelType(sim.model_type),
        scenario=ScenarioType(sim.scenario) if sim.scenario else None,
        rebalance_frequency=RebalanceFrequency(sim.rebalance_frequency) if sim.rebalance_frequency else None,
        mu_type=MuType(sim.mu_type),
        sample_paths_count=sim.sample_paths_count,
        ruin_threshold=sim.ruin_threshold,
        ruin_threshold_type=RuinThresholdType(sim.ruin_threshold_type),
        metrics=MetricsSummaryResponse(**sim.metrics),
        sample_paths=[SamplePathResponse(**path) for path in sim.sample_paths],
        created_at=sim.created_at,
    )


def _simulation_to_summary(sim: Simulation) -> SimulationSummaryResponse:
    """Convert a Simulation model to a SimulationSummaryResponse (no sample_paths)."""
    return SimulationSummaryResponse(
        id=sim.id,
        portfolio_id=sim.portfolio_id,
        name=sim.name,
        horizon_years=sim.horizon_years,
        num_paths=sim.num_paths,
        model_type=ModelType(sim.model_type),
        scenario=ScenarioType(sim.scenario) if sim.scenario else None,
        mu_type=MuType(sim.mu_type),
        metrics=MetricsSummaryResponse(**sim.metrics),
        created_at=sim.created_at,
    )


@router.post(
    "/portfolios/{portfolio_id}/simulations",
    response_model=SimulationResponse,
    summary="Run and save portfolio simulation",
    description="""
Run Monte Carlo simulation for a portfolio and save results.

Models available:
- gaussian: Standard multivariate normal returns
- student_t: Fat-tailed returns for better tail risk modeling
- regime_switching: Two-regime (calm/crisis) model

Scenarios available:
- japan_lost_decade: Low returns, poor equity performance
- stagflation: High volatility, reduced returns, increased correlations
""",
)
async def run_simulation(
    portfolio_id: UUID,
    request: SimulationRequest,
    current_user: Annotated[User, Depends(get_current_user_full)],
    simulation_service: Annotated[SimulationService, Depends(get_simulation_service)],
    simulation_repo: Annotated[SimulationRepository, Depends(get_simulation_repository)],
) -> SimulationResponse:
    """Run Monte Carlo simulation for a portfolio and save to database.

    Returns saved simulation with ID, metrics, and representative paths.
    """
    try:
        # Run simulation in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            _executor,
            lambda: simulation_service.run_simulation(
                portfolio_id=portfolio_id,
                user_id=current_user.id,
                horizon_years=request.horizon_years,
                num_paths=request.num_paths,
                model_type=request.model_type.value,
                scenario=request.scenario.value if request.scenario else None,
                rebalance_frequency=request.rebalance_frequency.value if request.rebalance_frequency else None,
                mu_type=request.mu_type.value,
                sample_paths_count=request.sample_paths_count,
                ruin_threshold=request.ruin_threshold,
                ruin_threshold_type=request.ruin_threshold_type.value,
                is_admin=current_user.is_admin,
            ),
        )

        # Create simulation entity for persistence
        simulation = Simulation(
            id=uuid4(),
            portfolio_id=portfolio_id,
            name=request.name,
            horizon_years=request.horizon_years,
            num_paths=request.num_paths,
            model_type=request.model_type.value,
            scenario=request.scenario.value if request.scenario else None,
            rebalance_frequency=request.rebalance_frequency.value if request.rebalance_frequency else None,
            mu_type=request.mu_type.value,
            sample_paths_count=request.sample_paths_count,
            ruin_threshold=request.ruin_threshold,
            ruin_threshold_type=request.ruin_threshold_type.value,
            metrics=result["metrics"],
            sample_paths=result["sample_paths"],
            created_at=datetime.now(timezone.utc),
        )

        # Save to database
        saved_simulation = simulation_repo.create(simulation)

        return _simulation_to_response(saved_simulation)

    except SimulationError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg,
            )
        elif "access denied" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error_msg,
            )
        elif "no holdings" in error_msg.lower() or "no valid" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=error_msg,
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Simulation failed: {str(e)}",
        )


@router.get(
    "/portfolios/{portfolio_id}/simulations",
    response_model=list[SimulationSummaryResponse],
    summary="List simulations for portfolio",
)
async def list_simulations(
    portfolio_id: UUID,
    current_user: Annotated[User, Depends(get_current_user_full)],
    simulation_repo: Annotated[SimulationRepository, Depends(get_simulation_repository)],
    portfolio_repo: Annotated[PortfolioRepository, Depends(get_portfolio_repository)],
) -> list[SimulationSummaryResponse]:
    """List all simulations for a portfolio."""
    # Verify portfolio access
    portfolio = portfolio_repo.get_by_id(portfolio_id)
    if portfolio is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio {portfolio_id} not found",
        )
    if not current_user.is_admin and portfolio.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this portfolio",
        )

    simulations = simulation_repo.get_by_portfolio_id(portfolio_id)
    return [_simulation_to_summary(sim) for sim in simulations]


@router.get(
    "/simulations/{simulation_id}",
    response_model=SimulationResponse,
    summary="Get simulation details",
)
async def get_simulation(
    simulation_id: UUID,
    current_user: Annotated[User, Depends(get_current_user_full)],
    simulation_repo: Annotated[SimulationRepository, Depends(get_simulation_repository)],
    portfolio_repo: Annotated[PortfolioRepository, Depends(get_portfolio_repository)],
) -> SimulationResponse:
    """Get full simulation details including sample paths."""
    simulation = simulation_repo.get_by_id(simulation_id)
    if simulation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Simulation {simulation_id} not found",
        )

    # Verify ownership via portfolio
    portfolio = portfolio_repo.get_by_id(simulation.portfolio_id)
    if portfolio is None or (not current_user.is_admin and portfolio.user_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this simulation",
        )

    return _simulation_to_response(simulation)


@router.delete(
    "/simulations/{simulation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete simulation",
)
async def delete_simulation(
    simulation_id: UUID,
    current_user: Annotated[User, Depends(get_current_user_full)],
    simulation_repo: Annotated[SimulationRepository, Depends(get_simulation_repository)],
    portfolio_repo: Annotated[PortfolioRepository, Depends(get_portfolio_repository)],
) -> None:
    """Delete a simulation."""
    # Get portfolio_id for ownership check
    portfolio_id = simulation_repo.get_portfolio_id_for_simulation(simulation_id)
    if portfolio_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Simulation {simulation_id} not found",
        )

    # Verify ownership
    portfolio = portfolio_repo.get_by_id(portfolio_id)
    if portfolio is None or (not current_user.is_admin and portfolio.user_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this simulation",
        )

    simulation_repo.delete(simulation_id)


@router.patch(
    "/simulations/{simulation_id}",
    response_model=SimulationResponse,
    summary="Rename simulation",
)
async def rename_simulation(
    simulation_id: UUID,
    request: SimulationRenameRequest,
    current_user: Annotated[User, Depends(get_current_user_full)],
    simulation_repo: Annotated[SimulationRepository, Depends(get_simulation_repository)],
    portfolio_repo: Annotated[PortfolioRepository, Depends(get_portfolio_repository)],
) -> SimulationResponse:
    """Rename a simulation."""
    # Get portfolio_id for ownership check
    portfolio_id = simulation_repo.get_portfolio_id_for_simulation(simulation_id)
    if portfolio_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Simulation {simulation_id} not found",
        )

    # Verify ownership
    portfolio = portfolio_repo.get_by_id(portfolio_id)
    if portfolio is None or (not current_user.is_admin and portfolio.user_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this simulation",
        )

    updated = simulation_repo.update_name(simulation_id, request.name)
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Simulation {simulation_id} not found",
        )

    return _simulation_to_response(updated)
