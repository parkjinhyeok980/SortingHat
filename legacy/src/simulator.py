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
