"""CSV loading and validation for employee Big Five data."""

from pathlib import Path

import pandas as pd

from src.config import (
    BIG5_COLUMNS,
    EMPLOYEE_ID_COLUMN,
    MAX_BIG5_SCORE,
    MIN_BIG5_SCORE,
    REQUIRED_COLUMNS,
)


def load_employees_csv(file_path: str | Path) -> pd.DataFrame:
    """Load employee CSV data and validate the required V1 schema.

    Args:
        file_path: Path to a CSV file containing employee information and Big Five scores.

    Returns:
        A validated pandas DataFrame.

    Raises:
        ValueError: If required columns, null values, duplicate IDs, or invalid scores are found.
    """
    employees = pd.read_csv(file_path)
    validate_employees(employees)
    return employees


def validate_employees(employees: pd.DataFrame) -> None:
    """Validate employee data for the current Big Five analysis scope."""
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in employees.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    if employees[REQUIRED_COLUMNS].isna().any().any():
        null_columns = employees[REQUIRED_COLUMNS].columns[
            employees[REQUIRED_COLUMNS].isna().any()
        ].tolist()
        raise ValueError(f"Missing values found in columns: {null_columns}")

    duplicated_ids = employees.loc[
        employees[EMPLOYEE_ID_COLUMN].duplicated(), EMPLOYEE_ID_COLUMN
    ].tolist()
    if duplicated_ids:
        raise ValueError(f"Duplicate employee_id values found: {duplicated_ids}")

    invalid_score_mask = ~employees[BIG5_COLUMNS].apply(
        lambda column: column.between(MIN_BIG5_SCORE, MAX_BIG5_SCORE)
    )
    if invalid_score_mask.any().any():
        invalid_columns = invalid_score_mask.columns[invalid_score_mask.any()].tolist()
        raise ValueError(
            "Big Five scores must be between "
            f"{MIN_BIG5_SCORE} and {MAX_BIG5_SCORE}. Invalid columns: {invalid_columns}"
        )
