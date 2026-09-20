"""Run the V1 Big Five team composition simulation."""

from src.config import BIG5_COLUMNS, SAMPLE_EMPLOYEES_CSV
from src.data_loader import load_employees_csv
from src.simulator import (
    analyze_team_candidates,
    get_top_diversity_teams,
    get_top_similarity_teams,
)
from src.team_generator import generate_teams


def format_team_results(results, top_n: int = 5):
    """Return compact columns for console output."""
    mean_columns = [f"{trait}_mean" for trait in BIG5_COLUMNS]
    return results[
        [
            "team_id",
            "member_ids",
            "member_names",
            "personality_similarity_score",
            "personality_diversity_score",
            *mean_columns,
        ]
    ].head(top_n)


def main() -> None:
    """Load sample employees, generate teams, analyze them, and print top candidates."""
    employees = load_employees_csv(SAMPLE_EMPLOYEES_CSV)
    print(f"Loaded employees: {len(employees)}")

    team_size = 5
    teams = generate_teams(employees, team_size=team_size)
    results = analyze_team_candidates(teams)
    print(f"Generated team candidates: {len(results)}")

    print("\nTop 5 teams by personality similarity indicator")
    top_similarity = get_top_similarity_teams(results, top_n=5)
    print(format_team_results(top_similarity).to_string(index=False))

    print("\nTop 5 teams by personality diversity indicator")
    top_diversity = get_top_diversity_teams(results, top_n=5)
    print(format_team_results(top_diversity).to_string(index=False))


if __name__ == "__main__":
    main()
