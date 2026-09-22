"""Run competency matching with item-level PG-fit references."""
from src.config import SAMPLE_EMPLOYEES_CSV
from src.data_loader import load_employees_csv
from src.team_generator import generate_teams
from src.simulator import analyze_team_candidates
from src.project_fit import analyze_project_candidates, rank_project_candidates, PRESETS


def main():
    employees = load_employees_csv(SAMPLE_EMPLOYEES_CSV)
    teams = list(generate_teams(employees, team_size=5))
    preset = PRESETS["신규 서비스 출시"]
    results = analyze_project_candidates(teams, preset["skills"], preset["roles"])
    references = analyze_team_candidates(teams).drop(columns=["member_ids", "member_names"])
    results = results.merge(references, on="team_id", validate="one_to_one")
    print(rank_project_candidates(results).head(5).to_string(index=False))


if __name__ == "__main__":
    main()
