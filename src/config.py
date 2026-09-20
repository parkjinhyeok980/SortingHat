"""Project-wide constants for the Gryffindor Hat analysis."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
SAMPLE_EMPLOYEES_CSV = DATA_DIR / "employees_sample.csv"

EMPLOYEE_ID_COLUMN = "employee_id"
NAME_COLUMN = "name"
RANK_COLUMN = "rank"
DEPARTMENT_COLUMN = "current_department"

BIG5_COLUMNS = [
    "extraversion",
    "agreeableness",
    "conscientiousness",
    "openness",
    "emotional_stability",
]

REQUIRED_COLUMNS = [
    EMPLOYEE_ID_COLUMN,
    NAME_COLUMN,
    RANK_COLUMN,
    DEPARTMENT_COLUMN,
    *BIG5_COLUMNS,
]

MIN_BIG5_SCORE = 0
MAX_BIG5_SCORE = 100
