"""사전 정의한 조직 점검 집단. 관찰 차이를 정책 효과로 오인하지 않는다."""
import pandas as pd
from scipy.stats import fisher_exact
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.proportion import proportion_confint


def actions(df):
    candidates = []
    def add(column, name, mask, policy, metric):
        if column in df:
            candidates.append((name, mask, df[column].notna(), policy, metric))
    if 'YearsAtCompany' in df:
        add('YearsAtCompany', '저연차(근속 ≤2년)', df.YearsAtCompany <= 2, '온보딩·멘토링 운영 및 초기 적응 면담 점검', '입사 12개월 유지율')
    if 'OverTime' in df:
        add('OverTime', '초과근무(Yes)', df.OverTime == 'Yes', '업무량·근무시간·인력배치 점검', '초과근무 시간, 조직별 유지율')
    if 'YearsSinceLastPromotion' in df:
        add('YearsSinceLastPromotion', '승진대기(≥5년)', df.YearsSinceLastPromotion >= 5, '직급·근속을 고려한 경력경로 및 승진 기회 점검', '내부 이동률, 경력개발 만족도')
    if 'JobSatisfaction' in df:
        add('JobSatisfaction', '직무만족도 낮음(≤2)', df.JobSatisfaction <= 2, '익명 설문과 집단 면담으로 직무·환경 개선 과제 확인', '익명 만족도, 집단 유지율')
    if {'MonthlyIncome', 'JobLevel'} <= set(df):
        threshold = df.groupby('JobLevel').MonthlyIncome.transform(lambda s: s.quantile(.25))
        mask = (df.MonthlyIncome <= threshold) & df.JobLevel.notna()
        add('MonthlyIncome', '동일 직급 급여 하위 25%', mask, '직무·경력·시장 임금 차이를 추가 확인한 보상체계 점검', '보상 공정성 인식, 집단 유지율')
        candidates[-1] = (candidates[-1][0], mask, df.MonthlyIncome.notna() & df.JobLevel.notna(), *candidates[-1][3:])
    rows = []
    for name, mask, known, policy, metric in candidates:
        a, b = df.loc[mask & known, 'Attrition'], df.loc[~mask & known, 'Attrition']
        if min(len(a), len(b)) < 1:
            continue
        low, high = proportion_confint(a.sum(), len(a), method='wilson')
        _, p = fisher_exact([[a.sum(), len(a)-a.sum()], [b.sum(), len(b)-b.sum()]])
        rows.append({'group': name, 'n': len(a), 'leavers': int(a.sum()), 'rate': a.mean(),
                     'CI_low': low, 'CI_high': high, 'rest_rate': b.mean(), 'difference_pp': 100*(a.mean()-b.mean()),
                     'p_value': p, 'policy': policy, 'follow_up_metric': metric})
    result = pd.DataFrame(rows)
    if not result.empty:
        result['p_holm'] = multipletests(result.p_value, method='holm')[1]
        result['priority'] = result.apply(lambda r: '우선 점검' if r.n >= 30 and r.difference_pp > 0 and r.p_holm < .05 else '추가 확인', axis=1)
        result = result.sort_values(['priority', 'difference_pp'], ascending=[True, False])
    return result
