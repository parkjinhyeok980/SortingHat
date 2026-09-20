import pandas as pd

from src.team_metrics import analyze_team, calculate_pairwise_distances


def test_pairwise_distances_for_two_members() -> None:
    team = pd.DataFrame(
        [
            {
                "employee_id": "E001",
                "name": "직원01",
                "rank": "팀장",
                "current_department": "인사",
                "extraversion": 0,
                "agreeableness": 0,
                "conscientiousness": 0,
                "openness": 0,
                "emotional_stability": 0,
            },
            {
                "employee_id": "E002",
                "name": "직원02",
                "rank": "사원",
                "current_department": "기획",
                "extraversion": 3,
                "agreeableness": 4,
                "conscientiousness": 0,
                "openness": 0,
                "emotional_stability": 0,
            },
        ]
    )

    distances = calculate_pairwise_distances(team)

    assert distances == [5.0]


def test_analyze_team_returns_core_metrics() -> None:
    team = pd.DataFrame(
        [
            {
                "employee_id": "E001",
                "name": "직원01",
                "rank": "팀장",
                "current_department": "인사",
                "extraversion": 70,
                "agreeableness": 80,
                "conscientiousness": 90,
                "openness": 60,
                "emotional_stability": 75,
            },
            {
                "employee_id": "E002",
                "name": "직원02",
                "rank": "사원",
                "current_department": "기획",
                "extraversion": 50,
                "agreeableness": 60,
                "conscientiousness": 70,
                "openness": 80,
                "emotional_stability": 65,
            },
        ]
    )

    result = analyze_team(team)

    assert result["member_ids"] == ["E001", "E002"]
    assert result["extraversion_mean"] == 60.0
    assert result["extraversion_range"] == 20.0
    assert result["personality_diversity_score"] > 0
    assert 0 < result["personality_similarity_score"] <= 1
