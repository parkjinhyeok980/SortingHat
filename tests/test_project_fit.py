import pytest

from app import read_data
from src.config import SAMPLE_EMPLOYEES_CSV, BIG5_COLUMNS
from src.project_fit import analyze_project_candidates


def test_skill_and_role_coverage_stays_independent_of_personality():
    team = read_data(SAMPLE_EMPLOYEES_CSV.read_bytes()).iloc[:2].copy()
    team["planning"] = [40, 60]
    team["engineering"] = [20, 30]
    team["role"] = ["기획", "디자인"]
    result = analyze_project_candidates([team], ["planning", "engineering"], ["기획", "개발"], 60).iloc[0]
    assert result.skill_score == pytest.approx(75)
    assert result.role_score == pytest.approx(50)
    assert result.fit_score == pytest.approx(67.5 + result.sharing_bonus)
    assert result.missing_skills == ["개발"]
    assert result.missing_roles == ["개발"]
    team[BIG5_COLUMNS] = 100
    changed = analyze_project_candidates([team], ["planning", "engineering"], ["기획", "개발"], 60).iloc[0]
    assert changed.fit_score == result.fit_score


from src.project_fit import SKILLS, rank_project_candidates


def make_team(scores):
    team = read_data(SAMPLE_EMPLOYEES_CSV.read_bytes()).iloc[:len(scores)].copy()
    team[list(SKILLS)] = scores
    return team


def test_complementary_specialists_beat_one_expert_with_same_maxima():
    balanced = make_team([[90, 60, 20, 10, 10], [60, 90, 20, 10, 10]])
    concentrated = make_team([[90, 90, 20, 10, 10], [60, 60, 20, 10, 10]])
    results = analyze_project_candidates([concentrated, balanced], ["planning", "design"], ["기획"], 70)
    assert results.iloc[1].complementarity_score == 100
    assert results.iloc[0].complementarity_score < 100
    # Even an artificially larger secondary score cannot override complementarity.
    results.loc[0, "fit_score"] = 110
    assert rank_project_candidates(results).iloc[0].team_id == "T0002"


def test_secondary_strength_adds_bonus_and_breaks_coverage_tie():
    isolated = make_team([[90, 10, 5, 5, 5], [10, 90, 5, 5, 5]])
    connected = make_team([[90, 60, 5, 5, 5], [60, 90, 5, 5, 5]])
    results = analyze_project_candidates([isolated, connected], ["planning", "design"], ["기획"], 70)
    assert results.complementarity_score.tolist() == [100, 100]
    assert results.iloc[0].sharing_bonus == 0
    assert results.iloc[1].sharing_bonus == pytest.approx(10 * 60 / 70)
    assert len(results.iloc[1].sharing_links) == 2
    assert rank_project_candidates(results).iloc[0].team_id == "T0002"


def test_weak_second_skill_and_equal_experts_do_not_get_bonus():
    weak = make_team([[90, 20, 5, 5, 5], [20, 90, 5, 5, 5]])
    equal = make_team([[90, 90, 5, 5, 5], [90, 90, 5, 5, 5]])
    results = analyze_project_candidates([weak, equal], ["planning", "design"], ["기획"], 70)
    assert results.sharing_bonus.tolist() == [0, 0]


def test_high_third_skill_qualifies_and_missing_specialists_reduce_coverage():
    team = make_team([[95, 90, 60, 5, 5], [10, 10, 90, 5, 5]])
    result = analyze_project_candidates([team], ["planning", "design", "engineering"], ["기획"], 70).iloc[0]
    assert result.complementarity_score == pytest.approx(200 / 3)
    assert len(result.sharing_links) == 1
    assert result.sharing_bonus > 0
