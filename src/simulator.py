"""Simulation helpers for comparing generated team candidates."""

from collections.abc import Iterable

import pandas as pd

from src.team_metrics import analyze_team


def analyze_team_candidates(teams: Iterable[pd.DataFrame]) -> pd.DataFrame:
    """Analyze many team candidates and return one row per candidate."""
    rows = []
    for team_number, team in enumerate(teams, start=1):
        row = {"team_id": f"T{team_number:04d}"}
        row.update(analyze_team(team))
        rows.append(row)

    return pd.DataFrame(rows)


def get_top_similarity_teams(results: pd.DataFrame, top_n: int = 5) -> pd.DataFrame:
    """Return teams with the highest personality similarity indicator."""
    return results.sort_values("personality_similarity_score", ascending=False).head(top_n)


def get_top_diversity_teams(results: pd.DataFrame, top_n: int = 5) -> pd.DataFrame:
    """Return teams with the highest personality diversity indicator."""
    return results.sort_values("personality_diversity_score", ascending=False).head(top_n)
