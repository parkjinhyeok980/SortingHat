"""Exercise the interactive analysis flow and invalid CSV handling."""

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from app import read_data
from src.config import PROJECT_ROOT, SAMPLE_EMPLOYEES_CSV


def test_csv_rejects_invalid_scores():
    employees = pd.read_csv(SAMPLE_EMPLOYEES_CSV)
    employees["value_quality"] = employees["value_quality"].astype(float)
    employees.loc[0, "value_quality"] = float("inf")
    with pytest.raises(ValueError):
        read_data(employees.to_csv(index=False).encode("utf-8"))


def test_analysis_and_changed_inputs():
    app = AppTest.from_file(PROJECT_ROOT / "app.py", default_timeout=60).run()
    assert not app.exception
    app.number_input[0].set_value(2).run()
    app.button[0].click().run()
    assert not app.exception
    assert len(app.session_state['analysis_results']) == 190
    assert not app.exception
    assert len(app.dataframe) >= 3
    app.number_input[0].set_value(3).run()
    assert not app.exception
    assert not app.radio


def test_rank_constraints_and_empty_department_selection():
    app = AppTest.from_file(PROJECT_ROOT / "app.py", default_timeout=60).run()
    app.checkbox[0].check().run()
    app.button[0].click().run()
    assert not app.exception
    assert len(app.session_state['analysis_results']) == 576
    app.multiselect[0].set_value([]).run()
    assert not app.exception
    assert app.info


@pytest.mark.parametrize("column,value", [("engineering", -1), ("analytics", 101), ("planning", "invalid"), ("availability", float("inf"))])
def test_csv_rejects_invalid_competencies(column, value):
    employees = pd.read_csv(SAMPLE_EMPLOYEES_CSV).astype({column: object})
    employees.loc[0, column] = value
    with pytest.raises(ValueError):
        read_data(employees.to_csv(index=False).encode("utf-8"))


def test_requirements_change_invalidates_combined_results():
    app = AppTest.from_file(PROJECT_ROOT / "app.py", default_timeout=60).run()
    app.number_input[0].set_value(2).run()
    app.button[0].click().run()
    results = app.session_state["analysis_results"]
    assert {"fit_score", "skill_score", "role_score", "value_quality_range"} <= set(results.columns)
    assert results.fit_score.between(0, 110).all()
    app.slider[0].set_value(90).run()
    assert "analysis_results" not in app.session_state
    app.multiselect[1].set_value([]).run()
    assert app.button[0].disabled
    assert not app.exception


@pytest.mark.parametrize("column,value", [("value_quality", 0), ("observed_support_need", 6), ("perceived_values", 2.5), ("perceived_needs", "invalid"), ("perceived_goals", None)])
def test_survey_scale_validation(column, value):
    employees = pd.read_csv(SAMPLE_EMPLOYEES_CSV).astype({column: object})
    employees.loc[0, column] = value
    with pytest.raises(ValueError, match="1~5"):
        read_data(employees.to_csv(index=False).encode("utf-8"))


def test_missing_survey_and_team_context_rejected():
    employees = pd.read_csv(SAMPLE_EMPLOYEES_CSV)
    with pytest.raises(ValueError, match="필수 설문"):
        read_data(employees.drop(columns="perceived_values").to_csv(index=False).encode("utf-8"))
    employees.loc[0, "current_team_id"] = " "
    with pytest.raises(ValueError, match="current_team_id"):
        read_data(employees.to_csv(index=False).encode("utf-8"))
