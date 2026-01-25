from abc import ABC, abstractmethod
from uuid import UUID

from domain.models.simulation import Simulation


class SimulationRepository(ABC):
    """Port for simulation persistence operations."""

    @abstractmethod
    def create(self, simulation: Simulation) -> Simulation:
        """Persist a new simulation."""
        pass

    @abstractmethod
    def get_by_id(self, id: UUID) -> Simulation | None:
        """Retrieve a simulation by ID."""
        pass

    @abstractmethod
    def get_by_portfolio_id(self, portfolio_id: UUID) -> list[Simulation]:
        """Retrieve all simulations for a portfolio."""
        pass

    @abstractmethod
    def update_name(self, id: UUID, name: str) -> Simulation | None:
        """Update simulation name."""
        pass

    @abstractmethod
    def delete(self, id: UUID) -> bool:
        """Delete a simulation by ID. Returns True if deleted."""
        pass

    @abstractmethod
    def get_portfolio_id_for_simulation(self, id: UUID) -> UUID | None:
        """Get the portfolio_id for a simulation (for ownership checks)."""
        pass
