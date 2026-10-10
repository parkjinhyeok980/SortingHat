"""Validate competencies and anchored 1–5 survey responses."""
from pathlib import Path
import pandas as pd
from src.config import REQUIRED_COLUMNS, SURVEY_COLUMNS
from src.project_fit import read_project_data


def validate_employees(employees):
    missing = [c for c in REQUIRED_COLUMNS if c not in employees]
    if missing:
        raise ValueError(f"필수 설문 열이 없습니다: {', '.join(missing)}")
    for column in ["employee_id", "name", "rank", "current_department", "current_team_id"]:
        if employees[column].isna().any() or employees[column].astype(str).str.strip().eq("").any():
            raise ValueError(f"{column}에 빈 값이 있습니다.")
    if employees.employee_id.duplicated().any():
        raise ValueError("직원 ID는 중복될 수 없습니다.")
    for column in SURVEY_COLUMNS:
        values = pd.to_numeric(employees[column], errors="coerce")
        if not (values.between(1, 5) & values.mod(1).eq(0)).all():
            raise ValueError(f"{column}: 설문 응답은 1~5 사이의 정수여야 합니다.")


def read_employees(raw):
    employees = read_project_data(raw)
    validate_employees(employees)
    employees[SURVEY_COLUMNS] = employees[SURVEY_COLUMNS].apply(pd.to_numeric)
    return employees.reset_index(drop=True)


def load_employees_csv(file_path: str | Path):
    return read_employees(Path(file_path).read_bytes())
