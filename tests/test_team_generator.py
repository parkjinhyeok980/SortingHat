import pandas as pd

from src.team_generator import generate_teams, generate_teams_with_rank_constraints


def sample_employees() -> pd.DataFrame:
    """Create small employee data for generator tests."""
    return pd.DataFrame(
        [
            {"employee_id": "E001", "name": "A", "rank": "팀장", "current_department": "인사"},
            {"employee_id": "E002", "name": "B", "rank": "대리", "current_department": "기획"},
            {"employee_id": "E003", "name": "C", "rank": "대리", "current_department": "재무"},
            {"employee_id": "E004", "name": "D", "rank": "사원", "current_department": "영업"},
            {"employee_id": "E005", "name": "E", "rank": "사원", "current_department": "인사"},
        ]
    )


def test_generate_teams_without_constraints() -> None:
    employees = sample_employees()

    teams = list(generate_teams(employees, team_size=2))

    assert len(teams) == 10
    assert teams[0]["employee_id"].tolist() == ["E001", "E002"]


def test_generate_teams_with_rank_constraints() -> None:
    employees = sample_employees()

    teams = list(generate_teams_with_rank_constraints(employees, {"팀장": 1, "대리": 1, "사원": 1}))

    assert len(teams) == 4
    for team in teams:
        assert team["rank"].value_counts().to_dict() == {"팀장": 1, "대리": 1, "사원": 1}
