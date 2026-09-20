"""Team-level Big Five analysis metrics."""

from collections.abc import Callable
from itertools import combinations
from typing import Any

import numpy as np
import pandas as pd

from src.config import BIG5_COLUMNS, EMPLOYEE_ID_COLUMN, NAME_COLUMN
from src.personality import distance_to_similarity, euclidean_distance_between_vectors

DistanceFunction = Callable[[list[float], list[float]], float]


def calculate_big5_means(team: pd.DataFrame) -> dict[str, float]:
    """Calculate mean score for each Big Five trait in a team."""
    return team[BIG5_COLUMNS].mean().to_dict()


def calculate_big5_std(team: pd.DataFrame) -> dict[str, float]:
    """Calculate standard deviation for each Big Five trait in a team."""
    return team[BIG5_COLUMNS].std(ddof=0).fillna(0.0).to_dict()


def calculate_big5_min(team: pd.DataFrame) -> dict[str, float]:
    """Calculate minimum score for each Big Five trait in a team."""
    return team[BIG5_COLUMNS].min().to_dict()


def calculate_big5_max(team: pd.DataFrame) -> dict[str, float]:
    """Calculate maximum score for each Big Five trait in a team."""
    return team[BIG5_COLUMNS].max().to_dict()


def calculate_big5_range(team: pd.DataFrame) -> dict[str, float]:
    """Calculate max-min range for each Big Five trait in a team."""
    return (team[BIG5_COLUMNS].max() - team[BIG5_COLUMNS].min()).to_dict()


def calculate_pairwise_distances(
    team: pd.DataFrame,
    distance_function: DistanceFunction = euclidean_distance_between_vectors,
) -> list[float]:
    """Calculate all pairwise personality distances for team members."""
    vectors = team[BIG5_COLUMNS].astype(float).to_numpy().tolist()
    return [
        distance_function(first_vector, second_vector)
        for first_vector, second_vector in combinations(vectors, 2)
    ]


def calculate_personality_diversity(pairwise_distances: list[float]) -> float:
    """Calculate a personality diversity indicator from pairwise distances.

    V1 uses average pairwise distance: larger values indicate more spread in
    Big Five composition. This is not a performance prediction.
    """
    if not pairwise_distances:
        return 0.0
    return float(np.mean(pairwise_distances))


def calculate_personality_similarity(pairwise_distances: list[float]) -> float:
    """Calculate a personality similarity indicator from pairwise distances.

    V1 converts the average pairwise distance into a bounded 0-1 style
    indicator. Smaller distances produce larger similarity values.
    """
    average_distance = calculate_personality_diversity(pairwise_distances)
    return distance_to_similarity(average_distance)


def summarize_pairwise_distances(pairwise_distances: list[float]) -> dict[str, float]:
    """Summarize team member personality distances."""
    if not pairwise_distances:
        return {
            "average_personality_distance": 0.0,
            "min_personality_distance": 0.0,
            "max_personality_distance": 0.0,
        }

    return {
        "average_personality_distance": float(np.mean(pairwise_distances)),
        "min_personality_distance": float(np.min(pairwise_distances)),
        "max_personality_distance": float(np.max(pairwise_distances)),
    }


def analyze_team(
    team: pd.DataFrame,
    distance_function: DistanceFunction = euclidean_distance_between_vectors,
) -> dict[str, Any]:
    """Return core Big Five composition metrics for one team."""
    pairwise_distances = calculate_pairwise_distances(team, distance_function)
    means = calculate_big5_means(team)
    stds = calculate_big5_std(team)
    mins = calculate_big5_min(team)
    maxes = calculate_big5_max(team)
    ranges = calculate_big5_range(team)

    result: dict[str, Any] = {
        "member_ids": team[EMPLOYEE_ID_COLUMN].tolist(),
        "member_names": team[NAME_COLUMN].tolist(),
        **summarize_pairwise_distances(pairwise_distances),
        "personality_similarity_score": calculate_personality_similarity(pairwise_distances),
        "personality_diversity_score": calculate_personality_diversity(pairwise_distances),
    }

    for trait in BIG5_COLUMNS:
        result[f"{trait}_mean"] = float(means[trait])
        result[f"{trait}_std"] = float(stds[trait])
        result[f"{trait}_min"] = float(mins[trait])
        result[f"{trait}_max"] = float(maxes[trait])
        result[f"{trait}_range"] = float(ranges[trait])

    return result
