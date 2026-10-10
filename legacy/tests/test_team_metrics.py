import pandas as pd
import pytest
from src.config import PREFERENCE_COLUMNS, SURVEY_COLUMNS, SAMPLE_EMPLOYEES_CSV
from src.data_loader import load_employees_csv
from src.team_metrics import analyze_team, compare_member_preferences
from src.sample_data import generate_sample


def sample_team():
    team = load_employees_csv(SAMPLE_EMPLOYEES_CSV).iloc[:2].copy()
    team.loc[team.index[0], PREFERENCE_COLUMNS] = 1
    team.loc[team.index[1], PREFERENCE_COLUMNS] = 5
    return team


def test_item_summary_preserves_extremes_without_fit_total():
    result = analyze_team(sample_team())
    assert result["value_quality_mean"] == 3
    assert result["value_quality_range"] == 4
    assert set(result) == {"member_ids", "member_names"} | {f"{c}_{stat}" for c in PREFERENCE_COLUMNS for stat in ["mean", "range"]}


def test_peer_reference_excludes_self_and_preserves_direction():
    comparison = compare_member_preferences(sample_team())
    assert comparison.iloc[0]["다른 팀원 평균"] == 5
    assert comparison.iloc[0]["차이 (본인−동료)"] == -4
    assert comparison.iloc[-1]["차이 (본인−동료)"] == 4


def test_current_team_experience_does_not_transfer_to_candidate():
    team = sample_team()
    before = analyze_team(team)
    columns = [c for c in SURVEY_COLUMNS if c not in PREFERENCE_COLUMNS]
    team[columns] = 1
    team["current_team_id"] = "OTHER"
    assert analyze_team(team) == before


def test_single_member_has_no_peer_comparison():
    comparison = compare_member_preferences(sample_team().iloc[:1])
    assert comparison["다른 팀원 평균"].isna().all()
    assert comparison["차이 (본인−동료)"].isna().all()
    with pytest.raises(ValueError):
        analyze_team(sample_team().iloc[:0])


def test_sample_is_reproducible_and_valid():
    pd.testing.assert_frame_equal(generate_sample(), generate_sample())
    employees = load_employees_csv(SAMPLE_EMPLOYEES_CSV)
    assert len(employees) == 20
    assert employees.employee_id.nunique() == 20
    assert employees[SURVEY_COLUMNS].isin([1, 2, 3, 4, 5]).all().all()
