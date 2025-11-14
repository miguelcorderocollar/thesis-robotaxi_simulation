"""
Tesla Robotaxi Simulation Model

This package contains the core simulation engine, configuration, and plotting utilities.
"""

from .config import SimulationConfig
from .core import run_simulation, SimulationResults
from .plots import (
    plot_area_series,
    plot_global_series,
    plot_3_areas,
    plot_percentage_graph
)

__all__ = [
    'SimulationConfig',
    'run_simulation',
    'SimulationResults',
    'plot_area_series',
    'plot_global_series',
    'plot_3_areas',
    'plot_percentage_graph',
]

