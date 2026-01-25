"""Scenario implementations for stress testing."""

from simulation.scenarios.base import Scenario
from simulation.scenarios.japan_lost_decade import JapanLostDecadeScenario
from simulation.scenarios.stagflation import StagflationScenario

__all__ = [
    "Scenario",
    "JapanLostDecadeScenario",
    "StagflationScenario",
]
