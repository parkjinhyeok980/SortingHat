"""사전 정의한 검정에 Holm 보정. 순서형 만족도는 순위 검정으로 보완한다."""
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.oneway import anova_oneway


def run_tests(df):
    rows = []
    def add(name, h0, h1, statistic, p, effect, note, n):
        rows.append(dict(test=name, H0=h0, H1=h1, statistic=float(statistic), p_value=float(p),
                         effect=effect, assumptions=note, n=n))
    for c in ['OverTime', 'Department']:
        if c not in df:
            continue
        tab = pd.crosstab(df[c], df.Attrition)
        if min(tab.shape) < 2:
            continue
        chi, p, dof, expected = stats.chi2_contingency(tab, correction=False)
        v = np.sqrt(chi / (tab.to_numpy().sum() * min(tab.shape[0]-1, tab.shape[1]-1)))
        note = f'독립 관측 가정; 자유도={dof}; 최소 기대빈도={expected.min():.2f}. Cramér V={v:.3f}'
        if expected.min() < 5:
            if tab.shape == (2, 2):
                odds, p = stats.fisher_exact(tab)
                add(f'{c} Fisher exact', '두 변수는 독립', '두 변수는 관련됨', odds, p, f'표본 OR={odds:.3f}', note, int(tab.to_numpy().sum()))
            else:
                # 희소한 다범주 검정 결과를 유의하다고 제시하지 않는다.
                continue
        else:
            add(f'{c} chi-square', '두 변수는 독립', '두 변수는 관련됨', chi, p, f'Cramér V={v:.3f}', note, int(tab.to_numpy().sum()))
    for c in ['MonthlyIncome', 'JobSatisfaction', 'YearsAtCompany']:
        if c not in df:
            continue
        a = df.loc[df.Attrition == 1, c].dropna().to_numpy()
        b = df.loc[df.Attrition == 0, c].dropna().to_numpy()
        if min(len(a), len(b)) < 2 or np.var(a) + np.var(b) == 0:
            continue
        t, p = stats.ttest_ind(a, b, equal_var=False)
        va, vb = a.var(ddof=1)/len(a), b.var(ddof=1)/len(b)
        dof = (va+vb)**2/(va**2/(len(a)-1)+vb**2/(len(b)-1))
        diff = a.mean()-b.mean()
        margin = stats.t.ppf(.975, dof)*np.sqrt(va+vb)
        pooled = np.sqrt(((len(a)-1)*a.var(ddof=1)+(len(b)-1)*b.var(ddof=1))/(len(a)+len(b)-2))
        g = (diff/pooled)*(1-3/(4*(len(a)+len(b))-9))
        effect = f'퇴사 평균={a.mean():.3f}, 재직 평균={b.mean():.3f}; 차이={diff:.3f}, 95% CI [{diff-margin:.3f}, {diff+margin:.3f}]; Hedges g={g:.3f}'
        add(f'{c} Welch t-test', '두 집단 평균은 같음', '두 집단 평균은 다름', t, p, effect,
            f'독립 관측, 평균의 표본분포 근사; 등분산 불필요; n(퇴사/재직)={len(a)}/{len(b)}', len(a)+len(b))
        if c == 'JobSatisfaction':
            u, p = stats.mannwhitneyu(a, b, alternative='two-sided')
            add('JobSatisfaction Mann–Whitney', '두 집단 분포는 같음', '두 집단 분포는 다름', u, p,
                f'rank-biserial(퇴사−재직)={2*u/(len(a)*len(b))-1:.3f}',
                '만족도는 순서형. 분포 형태가 같을 때만 위치 차이로 해석.', len(a)+len(b))
    if {'JobRole', 'JobSatisfaction'} <= set(df):
        groups = [g.JobSatisfaction.dropna().to_numpy() for _, g in df.groupby('JobRole')]
        if len(groups) >= 2 and all(len(g) >= 2 and g.var() > 0 for g in groups):
            result = anova_oneway(groups, use_var='unequal')
            means = [g.mean() for g in groups]
            add('JobRole → satisfaction Welch ANOVA', '직무별 평균 만족도는 모두 같음', '적어도 한 직무 평균이 다름',
                result.statistic, result.pvalue, f'직무 평균 범위={min(means):.3f}–{max(means):.3f}',
                '순서형 척도를 등간격으로 근사; 등분산 불필요. 유의해도 어느 직무 차이인지는 별도 검정 필요.', sum(map(len, groups)))
            h, p = stats.kruskal(*groups)
            add('JobRole → satisfaction Kruskal–Wallis', '직무별 분포는 같음', '적어도 한 직무 분포가 다름', h, p,
                f'epsilon²≈{max(0, (h-len(groups)+1)/(sum(map(len, groups))-len(groups))):.3f}',
                '순서형 만족도에 대한 민감도 분석; 독립 관측 가정.', sum(map(len, groups)))
    out = pd.DataFrame(rows)
    if not out.empty:
        out['p_holm'] = multipletests(out.p_value, method='holm')[1]
        out['alpha'] = .05
        out['decision'] = np.where(out.p_holm < .05, '귀무가설 기각', '귀무가설 기각 못함')
        out['HR_interpretation'] = np.where(out.p_holm < .05,
            '차이/관련성이 관찰되어 조직 운영 점검의 근거로 검토합니다. 효과크기와 현장 맥락을 함께 확인하세요.',
            '현재 표본에서 차이/관련성을 확인할 근거가 충분하지 않습니다. 차이가 없다는 증명은 아닙니다.')
    return out
