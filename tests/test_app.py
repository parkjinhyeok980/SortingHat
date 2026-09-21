"""Exercise the interactive analysis flow and invalid CSV handling."""

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from app import read_data
from src.config import PROJECT_ROOT, SAMPLE_EMPLOYEES_CSV


def test_csv_rejects_invalid_scores():
    employees = pd.read_csv(SAMPLE_EMPLOYEES_CSV)
    employees["extraversion"] = employees["extraversion"].astype(float)
    employees.loc[0, "extraversion"] = float("inf")
    with pytest.raises(ValueError):
        read_data(employees.to_csv(index=False).encode("utf-8"))


def test_analysis_and_changed_inputs():
    app = AppTest.from_file(PROJECT_ROOT / "app.py", default_timeout=60).run()
    assert not app.exception
    app.number_input[0].set_value(2).run()
    app.button[0].click().run()
    assert not app.exception
    assert len(app.session_state['analysis_results']) == 190
    app.radio[0].set_value("성향이 다양한 팀").run()
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
