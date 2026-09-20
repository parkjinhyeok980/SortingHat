"""Personality vector and distance utilities."""

from collections.abc import Sequence

import numpy as np
import pandas as pd

from src.config import BIG5_COLUMNS


def get_big5_vector(employee: pd.Series, columns: Sequence[str] = BIG5_COLUMNS) -> np.ndarray:
    """Return one employee's Big Five scores as a numeric vector."""
    return employee.loc[list(columns)].astype(float).to_numpy()


def euclidean_personality_distance(
    first_employee: pd.Series,
    second_employee: pd.Series,
    columns: Sequence[str] = BIG5_COLUMNS,
) -> float:
    """Calculate Euclidean distance between two employees' Big Five vectors."""
    first_vector = get_big5_vector(first_employee, columns)
    second_vector = get_big5_vector(second_employee, columns)
    return float(np.linalg.norm(first_vector - second_vector))


def euclidean_distance_between_vectors(
    first_vector: Sequence[float],
    second_vector: Sequence[float],
) -> float:
    """Calculate Euclidean distance between two numeric vectors."""
    return float(np.linalg.norm(np.asarray(first_vector, dtype=float) - np.asarray(second_vector, dtype=float)))


def distance_to_similarity(distance: float, max_distance: float | None = None) -> float:
    """Convert a distance value into a bounded similarity indicator.

    The current V1 formula is intentionally simple. It is an analysis indicator,
    not a team performance prediction score.
    """
    if distance < 0:
        raise ValueError("distance must be non-negative")

    if max_distance is not None:
        if max_distance <= 0:
            raise ValueError("max_distance must be positive")
        return max(0.0, 1.0 - distance / max_distance)

    return 1.0 / (1.0 + distance)
