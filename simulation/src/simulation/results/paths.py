"""Path selection and storage utilities."""

import numpy as np
from numpy.typing import NDArray

from simulation.types import SamplePath


def select_representative_paths(
    paths: list[NDArray[np.floating]],
    terminal_values: NDArray[np.floating],
    count: int,
) -> list[SamplePath]:
    """Select representative paths at evenly-spaced percentiles.

    Paths are ranked by terminal value and selected at percentiles
    that evenly span the distribution.

    Args:
        paths: List of all simulation paths
        terminal_values: Array of terminal values for ranking
        count: Number of paths to select

    Returns:
        List of SamplePath objects representing selected percentiles
    """
    if count <= 0 or len(paths) == 0:
        return []

    n_paths = len(paths)
    count = min(count, n_paths)

    # Sort indices by terminal value
    sorted_indices = np.argsort(terminal_values)

    # Calculate percentiles to select
    # For count=10: select at 5th, 15th, 25th, 35th, 45th, 55th, 65th, 75th, 85th, 95th
    percentiles = []
    step = 100 / count
    for i in range(count):
        p = int(step / 2 + i * step)
        percentiles.append(min(p, 99))

    selected_paths = []
    for p in percentiles:
        # Find path at this percentile
        idx = int((p / 100) * (n_paths - 1))
        path_idx = sorted_indices[idx]
        path = paths[path_idx]

        selected_paths.append(
            SamplePath(
                percentile=p,
                values=tuple(float(v) for v in path),
                terminal_value=float(path[-1]),
            )
        )

    return selected_paths
