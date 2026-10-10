import pandas as pd
from statsmodels.stats.proportion import proportion_confint


def add_bands(df):
    df = df.copy()
    specs = {'YearsAtCompany': ('TenureBand', [-1, 1, 3, 5, 10, float('inf')], ['0–1', '2–3', '4–5', '6–10', '11+']),
             'YearsSinceLastPromotion': ('PromotionBand', [-1, 0, 2, 5, float('inf')], ['0', '1–2', '3–5', '6+'])}
    for c, (name, bins, labels) in specs.items():
        if c in df:
            df[name] = pd.cut(df[c], bins, labels=labels)
    if 'MonthlyIncome' in df:
        # 동률 때문에 분위수 경계가 중복되면 실제 구간 수를 줄인다.
        df['IncomeBand'] = pd.qcut(df.MonthlyIncome, 4, duplicates='drop')
    return df


def rates(df, column):
    result = df.groupby(column, observed=True, dropna=False).Attrition.agg(n='size', leavers='sum').reset_index()
    result['rate'] = result.leavers / result.n
    result['ci_low'], result['ci_high'] = proportion_confint(result.leavers, result.n, method='wilson')
    result[column] = result[column].astype(str)
    return result


def interpretation(table, column):
    eligible = table[table.n >= 30]
    if eligible.empty:
        return '모든 집단이 30명 미만이어서 우선순위를 해석하기 어렵습니다.'
    row = eligible.loc[eligible.rate.idxmax()]
    context = {'Department': '부서별 업무량·직무 구성 차이를 함께 점검합니다.',
               'JobRole': '직무별 채용시장과 경력 기회 차이를 추가 확인합니다.',
               'JobLevel': '직급별 근속·보상 구성이 다른지 확인합니다.',
               'TenureBand': '초기 적응과 경력 단계별 지원 공백을 점검합니다.',
               'OverTime': '업무량·인력배치·근무시간의 실제 기록을 확인합니다.',
               'JobSatisfaction': '익명 면담으로 만족도 저하와 관련된 직무 경험을 확인합니다.',
               'IncomeBand': '급여 차이는 직급·직무·경력 구성의 차이일 수 있습니다.',
               'PromotionBand': '승진대기기간을 근속·직급과 함께 해석해야 합니다.'}.get(column, '')
    return (f'{column}의 {row[column]} 집단에서 관찰 퇴사율 {row.rate:.1%} '
            f'({int(row.leavers)}/{int(row.n)}명)이 가장 높습니다(30명 이상 집단 기준). '
            f'{context} 집단 차이가 원인을 입증하지는 않습니다.')
