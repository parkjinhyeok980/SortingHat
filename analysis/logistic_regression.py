"""탐색적 연관성 추론: p-value 기반 변수 선택이나 class weighting은 쓰지 않는다."""
import warnings
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor

FEATURES = ['OverTime', 'JobSatisfaction', 'EnvironmentSatisfaction', 'WorkLifeBalance',
            'YearsAtCompany', 'MonthlyIncome', 'DistanceFromHome', 'YearsSinceLastPromotion', 'Department']


def design(df):
    columns = [c for c in FEATURES if c in df]
    complete = df[['Attrition'] + columns].dropna().copy()
    x = complete[columns].copy()
    if 'MonthlyIncome' in x:
        x = x.rename(columns={'MonthlyIncome': 'MonthlyIncome_per_1000'})
        x['MonthlyIncome_per_1000'] /= 1000
    categorical = [c for c in ['OverTime', 'Department'] if c in x]
    references = {c: sorted(x[c].unique())[0] for c in categorical}
    x = pd.get_dummies(x, columns=categorical, drop_first=True, dtype=float).astype(float)
    x = x.loc[:, x.nunique() > 1]
    return complete, x, references


def fit_logistic(df):
    complete, x, references = design(df)
    if x.empty or complete.Attrition.nunique() < 2:
        raise ValueError('로지스틱 회귀를 위한 유효 자료가 부족합니다.')
    x = sm.add_constant(x, has_constant='add')
    if np.linalg.matrix_rank(x) < x.shape[1]:
        raise ValueError('설계행렬의 완전 다중공선성을 해소해야 합니다.')
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        model = sm.Logit(complete.Attrition, x).fit(disp=False, maxiter=200)
    if not model.mle_retvals['converged']:
        raise ValueError('회귀가 수렴하지 않아 오즈비를 해석할 수 없습니다.')
    ci = model.conf_int()
    table = pd.DataFrame({'variable': x.columns, 'coefficient': model.params.to_numpy(),
                          'OR': np.exp(model.params.to_numpy()), 'CI_low': np.exp(ci[0].to_numpy()),
                          'CI_high': np.exp(ci[1].to_numpy()), 'p_value': model.pvalues.to_numpy()})
    table = table[table.variable != 'const'].reset_index(drop=True)
    if not np.isfinite(table[['OR', 'CI_low', 'CI_high']].to_numpy()).all():
        raise ValueError('분리 또는 추정 불안정으로 유한한 오즈비 구간을 얻지 못했습니다.')
    vif = pd.DataFrame({'variable': x.columns[1:],
                        'VIF': [variance_inflation_factor(x.to_numpy(), i) for i in range(1, x.shape[1])]})
    return {'table': table, 'vif': vif, 'n': len(complete), 'excluded': len(df)-len(complete),
            'references': references, 'warnings': [str(w.message) for w in caught],
            'events_per_parameter': int(complete.Attrition.sum())/(x.shape[1]-1)}
