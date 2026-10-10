import io
import numpy as np
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest
from analysis.preprocessing import prepare, DATA_PATH, ROOT
from analysis.statistical_tests import run_tests
from analysis.logistic_regression import fit_logistic
from analysis.decision_tree import fit_tree
from analysis.retention import actions


def test_source_quality_and_target():
    df, audit = prepare()
    assert len(df) == 1470
    assert df.Attrition.sum() == 237
    assert 'EmployeeNumber' not in df
    assert set(audit['removed_columns']) == {'EmployeeNumber', 'EmployeeCount', 'Over18', 'StandardHours'}
    assert not audit['schema'].missing.sum()


def test_invalid_target_and_missing_optional_column():
    raw = pd.read_csv(DATA_PATH)
    raw.loc[0, 'Attrition'] = 'unknown'
    with pytest.raises(ValueError, match='Yes/No'):
        prepare(io.StringIO(raw.to_csv(index=False)))
    raw.loc[0, 'Attrition'] = 'Yes'
    df, audit = prepare(io.StringIO(raw.drop(columns='MonthlyIncome').to_csv(index=False)))
    assert 'MonthlyIncome' in audit['missing_requested_columns']
    assert not run_tests(df).test.str.contains('MonthlyIncome').any()


def test_inference_and_rule_denominators():
    df, _ = prepare()
    tests = run_tests(df)
    assert (tests.p_holm >= tests.p_value - 1e-12).all()
    assert tests.loc[tests.test == 'OverTime chi-square', 'p_holm'].iloc[0] < .05
    logistic = fit_logistic(df)
    assert np.isfinite(logistic['table'].OR).all()
    assert logistic['table'].set_index('variable').loc['OverTime_Yes'].CI_low > 1
    tree = fit_tree(df)
    assert tree['rules'].n.sum() == len(df)
    assert tree['rules'].leavers.sum() == df.Attrition.sum()
    assert tree['model'].get_depth() <= 3
    assert set(tree['rules'].query("split == 'validation'").leaf) <= set(tree['rules'].query("split == 'train'").leaf)
    action = actions(df)
    assert np.allclose(action.rate, action.leavers/action.n)
    assert (action.query("priority == '우선 점검'").difference_pp > 0).all()


def test_all_dashboard_pages():
    app = AppTest.from_file(ROOT / 'app.py', default_timeout=90).run()
    assert not app.exception
    for page in ['Attrition Diagnosis', 'Statistical Analysis', 'Attrition Drivers', 'HR Action']:
        app.sidebar.radio[0].set_value(page).run()
        assert not app.exception, page
