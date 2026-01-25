import json
from uuid import UUID

from domain.models.simulation import Simulation
from domain.ports.simulation_repository import SimulationRepository

from adapters.postgres.connection import PostgresConnectionPool


class PostgresSimulationRepository(SimulationRepository):
    """PostgreSQL implementation of SimulationRepository."""

    def __init__(self, pool: PostgresConnectionPool) -> None:
        self._pool = pool

    def create(self, simulation: Simulation) -> Simulation:
        """Persist a new simulation."""
        with self._pool.cursor() as cur:
            cur.execute(
                """
                INSERT INTO simulation (
                    id, portfolio_id, name, horizon_years, num_paths, model_type,
                    scenario, rebalance_frequency, mu_type, sample_paths_count,
                    ruin_threshold, ruin_threshold_type, metrics, sample_paths, created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, portfolio_id, name, horizon_years, num_paths, model_type,
                    scenario, rebalance_frequency, mu_type, sample_paths_count,
                    ruin_threshold, ruin_threshold_type, metrics, sample_paths, created_at
                """,
                (
                    simulation.id,
                    simulation.portfolio_id,
                    simulation.name,
                    simulation.horizon_years,
                    simulation.num_paths,
                    simulation.model_type,
                    simulation.scenario,
                    simulation.rebalance_frequency,
                    simulation.mu_type,
                    simulation.sample_paths_count,
                    simulation.ruin_threshold,
                    simulation.ruin_threshold_type,
                    json.dumps(simulation.metrics),
                    json.dumps(simulation.sample_paths),
                    simulation.created_at,
                ),
            )
            row = cur.fetchone()

        if row is None:
            raise RuntimeError("Failed to create simulation")

        return self._row_to_simulation(row)

    def get_by_id(self, id: UUID) -> Simulation | None:
        """Retrieve a simulation by ID."""
        with self._pool.cursor() as cur:
            cur.execute(
                """
                SELECT id, portfolio_id, name, horizon_years, num_paths, model_type,
                    scenario, rebalance_frequency, mu_type, sample_paths_count,
                    ruin_threshold, ruin_threshold_type, metrics, sample_paths, created_at
                FROM simulation
                WHERE id = %s
                """,
                (id,),
            )
            row = cur.fetchone()

        if row is None:
            return None

        return self._row_to_simulation(row)

    def get_by_portfolio_id(self, portfolio_id: UUID) -> list[Simulation]:
        """Retrieve all simulations for a portfolio."""
        with self._pool.cursor() as cur:
            cur.execute(
                """
                SELECT id, portfolio_id, name, horizon_years, num_paths, model_type,
                    scenario, rebalance_frequency, mu_type, sample_paths_count,
                    ruin_threshold, ruin_threshold_type, metrics, sample_paths, created_at
                FROM simulation
                WHERE portfolio_id = %s
                ORDER BY created_at DESC
                """,
                (portfolio_id,),
            )
            rows = cur.fetchall()

        return [self._row_to_simulation(row) for row in rows]

    def update_name(self, id: UUID, name: str) -> Simulation | None:
        """Update simulation name."""
        with self._pool.cursor() as cur:
            cur.execute(
                """
                UPDATE simulation
                SET name = %s
                WHERE id = %s
                RETURNING id, portfolio_id, name, horizon_years, num_paths, model_type,
                    scenario, rebalance_frequency, mu_type, sample_paths_count,
                    ruin_threshold, ruin_threshold_type, metrics, sample_paths, created_at
                """,
                (name, id),
            )
            row = cur.fetchone()

        if row is None:
            return None

        return self._row_to_simulation(row)

    def delete(self, id: UUID) -> bool:
        """Delete a simulation by ID. Returns True if deleted."""
        with self._pool.cursor() as cur:
            cur.execute(
                """
                DELETE FROM simulation
                WHERE id = %s
                RETURNING id
                """,
                (id,),
            )
            row = cur.fetchone()

        return row is not None

    def get_portfolio_id_for_simulation(self, id: UUID) -> UUID | None:
        """Get the portfolio_id for a simulation (for ownership checks)."""
        with self._pool.cursor() as cur:
            cur.execute(
                """
                SELECT portfolio_id
                FROM simulation
                WHERE id = %s
                """,
                (id,),
            )
            row = cur.fetchone()

        if row is None:
            return None

        return row[0]

    def _row_to_simulation(self, row: tuple) -> Simulation:
        """Convert a database row to a Simulation model."""
        return Simulation(
            id=row[0],
            portfolio_id=row[1],
            name=row[2],
            horizon_years=row[3],
            num_paths=row[4],
            model_type=row[5],
            scenario=row[6],
            rebalance_frequency=row[7],
            mu_type=row[8],
            sample_paths_count=row[9],
            ruin_threshold=row[10],
            ruin_threshold_type=row[11],
            metrics=row[12],
            sample_paths=row[13],
            created_at=row[14],
        )
