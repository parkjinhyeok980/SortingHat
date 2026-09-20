"""Team candidate generation utilities."""

from collections.abc import Iterator
from itertools import combinations, product

import pandas as pd

from src.config import RANK_COLUMN


def generate_teams(employees: pd.DataFrame, team_size: int) -> Iterator[pd.DataFrame]:
    """Generate all team combinations with the requested team size."""
    if team_size <= 0:
        raise ValueError("team_size must be positive")
    if team_size > len(employees):
        raise ValueError("team_size cannot exceed employee count")

    for indexes in combinations(employees.index, team_size):
        yield employees.loc[list(indexes)].reset_index(drop=True)


def generate_teams_with_rank_constraints(
    employees: pd.DataFrame,
    rank_constraints: dict[str, int],
) -> Iterator[pd.DataFrame]:
    """Generate teams that satisfy exact rank-count constraints.

    Example:
        {"팀장": 1, "대리": 2, "사원": 2}
    """
    if not rank_constraints:
        raise ValueError("rank_constraints must not be empty")
    if any(required_count < 0 for required_count in rank_constraints.values()):
        raise ValueError("rank constraint counts must be non-negative")

    grouped_combinations: list[list[tuple[int, ...]]] = []
    for rank, required_count in rank_constraints.items():
        rank_indexes = employees.index[employees[RANK_COLUMN] == rank].tolist()
        if required_count > len(rank_indexes):
            raise ValueError(
                f"Not enough employees for rank '{rank}': "
                f"required {required_count}, available {len(rank_indexes)}"
            )
        grouped_combinations.append(list(combinations(rank_indexes, required_count)))

    for rank_group_indexes in product(*grouped_combinations):
        indexes = [index for group in rank_group_indexes for index in group]
        yield employees.loc[indexes].reset_index(drop=True)
