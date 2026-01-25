"""Return model implementations."""

from simulation.models.base import ReturnModel
from simulation.models.gaussian import GaussianMVNModel
from simulation.models.student_t import StudentTMVNModel
from simulation.models.regime_switching import RegimeSwitchingModel

__all__ = [
    "ReturnModel",
    "GaussianMVNModel",
    "StudentTMVNModel",
    "RegimeSwitchingModel",
]
