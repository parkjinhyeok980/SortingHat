"""원자료를 보존하면서 품질을 진단한다. 이상치는 자동 제거하지 않는다."""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / 'data/raw/WA_Fn-UseC_-HR-Employee-Attrition.csv'
NUMERIC = ['Age', 'JobLevel', 'MonthlyIncome', 'JobSatisfaction',
           'EnvironmentSatisfaction', 'RelationshipSatisfaction', 'WorkLifeBalance',
           'YearsAtCompany', 'YearsInCurrentRole', 'YearsSinceLastPromotion',
           'YearsWithCurrManager', 'TrainingTimesLastYear', 'PerformanceRating',
           'DistanceFromHome', 'TotalWorkingYears']


def prepare(source=DATA_PATH):
    raw = pd.read_csv(source)
    df = raw.copy()
    df.columns = df.columns.str.strip()
    if df.columns.duplicated().any() or 'Attrition' not in df:
        raise ValueError('중복 컬럼 또는 Attrition 컬럼 누락을 확인하세요.')
    for c in df.select_dtypes(include=['object', 'str']).columns:
        df[c] = df[c].str.strip().replace('', np.nan)
    # 종속변수는 추정하거나 대치하지 않는다. 잘못된 레이블은 즉시 알린다.
    if not df.Attrition.dropna().isin(['Yes', 'No']).all():
        raise ValueError('Attrition은 Yes/No여야 합니다.')
    missing_target = int(df.Attrition.isna().sum())
    df = df.dropna(subset=['Attrition']).copy()
    df['Attrition'] = df.Attrition.map({'No': 0, 'Yes': 1}).astype(int)
    if df.Attrition.nunique() != 2:
        raise ValueError('퇴사자와 재직자 두 집단이 모두 필요합니다.')
    for c in NUMERIC:
        if c in df:
            df[c] = pd.to_numeric(df[c], errors='raise')
            if np.isinf(df[c].dropna()).any() or (df[c].dropna() < 0).any():
                raise ValueError(f'{c}: 무한대 또는 음수는 허용하지 않습니다.')
    for c in ['JobSatisfaction', 'EnvironmentSatisfaction', 'RelationshipSatisfaction', 'WorkLifeBalance']:
        if c in df and not df[c].dropna().isin([1, 2, 3, 4]).all():
            raise ValueError(f'{c}: 1~4 척도를 확인하세요.')
    if 'OverTime' in df and not df.OverTime.dropna().isin(['Yes', 'No']).all():
        raise ValueError('OverTime은 Yes/No여야 합니다.')
    audit = pd.DataFrame({'column': df.columns, 'dtype': [str(df[c].dtype) for c in df],
                          'missing': [int(df[c].isna().sum()) for c in df],
                          'unique': [int(df[c].nunique()) for c in df]})
    outliers = []
    for c in NUMERIC:
        if c in df:
            q1, q3 = df[c].quantile([.25, .75])
            outliers.append({'column': c, 'IQR_flags': int(((df[c] < q1-1.5*(q3-q1)) | (df[c] > q3+1.5*(q3-q1))).sum())})
    # 식별자와 상수는 설명력이 없다. 중복은 실제 별도 직원일 수 있어 보고만 한다.
    removed = [c for c in df if c != 'Attrition' and (c == 'EmployeeNumber' or df[c].nunique() <= 1)]
    df = df.drop(columns=removed)
    return df, {'rows_raw': len(raw), 'rows_used': len(df), 'missing_target_removed': missing_target,
                'duplicate_rows': int(raw.duplicated().sum()), 'removed_columns': removed,
                'missing_requested_columns': [c for c in NUMERIC + ['Department', 'JobRole', 'OverTime'] if c not in raw],
                'schema': audit, 'outliers': pd.DataFrame(outliers)}
