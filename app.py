"""HR 담당자를 위한 조직 수준 연관성 분석 대시보드."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import plotly.express as px
import streamlit as st
from sklearn.tree import plot_tree
from analysis.preprocessing import prepare, DATA_PATH
from analysis.eda import add_bands, rates, interpretation
from analysis.statistical_tests import run_tests
from analysis.logistic_regression import fit_logistic
from analysis.decision_tree import fit_tree
from analysis.retention import actions

st.set_page_config(page_title='HR Retention Analytics', page_icon='◈', layout='wide')


@st.cache_data
def load_data(file_bytes):
    import io
    return prepare(io.BytesIO(file_bytes))


@st.cache_data
def analyze(df):
    results = {'tests': run_tests(df), 'actions': actions(df)}
    for name, method in [('logistic', fit_logistic), ('tree', fit_tree)]:
        try:
            results[name] = method(df)
        except (ValueError, RuntimeError, np.linalg.LinAlgError) as exc:
            results[name] = {'error': str(exc)}
    return results


st.title('HR Retention Analytics')
st.caption('직원 이탈 영향요인 분석 및 Retention 전략 도출 · ADsP 분석 포트폴리오')
st.warning('공개 IBM HR 계열의 가상·교육용 데이터입니다. 실제 IBM 직원 현황이나 정책 효과를 뜻하지 않습니다. 관찰된 관련성은 인과관계가 아니며 개인 평가·퇴사자 지정에 사용하지 않습니다.')
df, audit = load_data(DATA_PATH.read_bytes())
results = analyze(df)
st.sidebar.title('분석 탐색')
page = st.sidebar.radio('분석 단계', ['Workforce Overview', 'Attrition Diagnosis', 'Statistical Analysis', 'Attrition Drivers', 'HR Action'])
st.sidebar.caption(f'분석 모집단: {len(df):,}명 · 필터 없는 전체 자료\n\n관찰기간 정보가 없어 퇴사율은 표본 내 퇴사 비율입니다. 연간 이직률이 아닙니다.')
st.sidebar.info('개별 직원 조회·예측 기능 없이 집단 단위 결과만 제공합니다.')

if page == 'Workforce Overview':
    st.header('01 · Workforce Overview')
    metrics = [('전체 직원 수', f'{len(df):,}명'), ('퇴사자 수', f'{df.Attrition.sum():,}명'), ('관찰 퇴사율', f'{df.Attrition.mean():.1%}')]
    for c, label in [('YearsAtCompany', '평균 근속연수'), ('MonthlyIncome', '평균 월급(원자료 단위)')]:
        if c in df:
            metrics.append((label, f'{df[c].mean():,.2f}'))
    for col, (label, value) in zip(st.columns(len(metrics)), metrics):
        col.metric(label, value)
    st.subheader('HR 문제 정의')
    st.write('어떤 근무환경·보상·근속·만족도 특성이 직원 이탈과 관련되는지 확인하고, 조직 차원의 점검과 정책 실험 우선순위를 제안합니다.')
    st.write('전처리 → 기술통계 → 가설검정 → 다변량 로지스틱 회귀 → 얕은 의사결정나무 → Retention 정책 가설')
    st.subheader('퇴사자와 재직자의 특성')
    cols = [c for c in ['Age', 'MonthlyIncome', 'YearsAtCompany', 'JobSatisfaction', 'EnvironmentSatisfaction', 'DistanceFromHome'] if c in df]
    summary = df.groupby('Attrition')[cols].agg(['mean', 'median', 'count'])
    summary.index = summary.index.map({0: '재직', 1: '퇴사'})
    st.dataframe(summary, width='stretch')
    st.caption('평균·중앙값·비결측 표본 수. 급여와 통근거리는 원자료 메타데이터의 단위가 확정되지 않아 통화/거리 단위를 임의로 붙이지 않습니다.')
    with st.expander('전처리 판단과 데이터 품질'):
        st.json({k: v for k, v in audit.items() if k not in ['schema', 'outliers']})
        st.dataframe(audit['schema'], width='stretch')
        st.dataframe(audit['outliers'], width='stretch')
        st.write('IQR 이상치 표시는 점검용입니다. 고연차·고보상은 실제 가능한 값이므로 제거하지 않습니다. 결측치는 단변량 분석별 제외, 모델은 선택 변수 완전사례 분석을 사용합니다. 식별자·상수만 제외하고 원본 CSV는 보존합니다.')

elif page == 'Attrition Diagnosis':
    st.header('02 · Attrition Diagnosis')
    banded = add_bands(df)
    labels = {'Department': '부서', 'JobRole': '직무', 'JobLevel': '직급', 'TenureBand': '근속연수', 'OverTime': '초과근무', 'JobSatisfaction': '직무만족도', 'IncomeBand': '급여 사분위 구간', 'PromotionBand': '마지막 승진 이후 연수'}
    for c, label in labels.items():
        if c not in banded:
            continue
        table = rates(banded, c)
        st.subheader(label)
        table['upper'], table['lower'] = table.ci_high-table.rate, table.rate-table.ci_low
        fig = px.bar(table, x=c, y='rate', error_y='upper', error_y_minus='lower', hover_data=['n', 'leavers'], color_discrete_sequence=['#236653'])
        fig.update_layout(yaxis_tickformat='.0%', xaxis_title=label, yaxis_title='관찰 퇴사율', height=360)
        fig.add_hline(y=df.Attrition.mean(), line_dash='dot', annotation_text='전체 비율')
        st.plotly_chart(fig, width='stretch')
        st.write(interpretation(table, c))
        with st.expander('집단 크기·95% Wilson 신뢰구간'):
            st.dataframe(table.drop(columns=['upper', 'lower']), width='stretch')
    st.caption('구간은 탐색 목적입니다. 오차막대 중첩 여부만으로 집단 차이의 유의성을 판정하지 않습니다. 0년 승진대기는 최근 승진과 무승진을 구별하지 못할 수 있습니다.')

elif page == 'Statistical Analysis':
    st.header('03 · Statistical Analysis')
    st.info('유의수준 0.05. 아래 검정 전체를 한 검정군으로 Holm 보정합니다. 독립 관측을 가정하며 표본 추출 방식은 알려져 있지 않습니다. 순서형 만족도는 순위 검정으로 보완합니다.')
    table = results['tests']
    st.dataframe(table[['test', 'n', 'statistic', 'p_value', 'p_holm', 'decision']], width='stretch')
    for row in table.to_dict('records'):
        with st.expander(row['test'] + ' · ' + row['decision']):
            st.write(f"H₀: {row['H0']} / H₁: {row['H1']}")
            st.write(f"검정통계량={row['statistic']:.4g}, p={row['p_value']:.4g}, Holm p={row['p_holm']:.4g}, α=0.05")
            st.write(row['effect'])
            st.caption(row['assumptions'])
            st.write(row['HR_interpretation'])
    st.download_button('검정 결과 CSV', table.to_csv(index=False).encode('utf-8-sig'), 'statistical_tests.csv')

elif page == 'Attrition Drivers':
    st.header('04 · Attrition Drivers')
    st.subheader('다른 선택 요인을 함께 고려한 로지스틱 회귀')
    result = results['logistic']
    if 'error' in result:
        st.error(result['error'])
    else:
        st.write(f"완전사례 {result['n']:,}명 · 결측 제외 {result['excluded']}명 · 계수당 퇴사 사건 수 {result['events_per_parameter']:.1f}")
        st.caption(f"기준집단: {result['references']}. 연속형은 1단위 증가, 급여는 1,000 원자료 단위 증가에 대한 OR입니다.")
        table = result['table'].copy()
        table['upper'], table['lower'] = table.CI_high-table.OR, table.OR-table.CI_low
        fig = px.scatter(table, x='OR', y='variable', error_x='upper', error_x_minus='lower', log_x=True)
        fig.add_vline(x=1, line_dash='dot')
        fig.update_layout(height=500, xaxis_title='Odds Ratio · 95% CI', yaxis_title='')
        st.plotly_chart(fig, width='stretch')
        st.dataframe(result['table'], width='stretch')
        st.write('OR>1은 퇴사 오즈가 높고 OR<1은 낮다는 관련성입니다. 확률 배수나 정책의 인과효과가 아닙니다. 신뢰구간은 탐색적·개별 95% 구간이며 회귀 p-value는 다중검정 보정 전입니다.')
        st.caption('근속·급여와 중복되는 직급/총경력/현재 직무기간은 기본 모델에서 제외했습니다. 부서·초과근무·만족도·워라밸·근속·급여·통근·승진대기를 통제하며, 연령 등 미포함 요인의 잔여 교란은 남습니다. 만족도 등은 선형 추세를 가정합니다. 서로 다른 단위의 OR로 중요도 순위를 매기지 않습니다.')
        with st.expander('다중공선성(VIF) 및 추정 주의점'):
            st.dataframe(result['vif'], width='stretch')
            st.write('VIF>5는 점검 신호이며 자동 삭제 기준은 아닙니다. 범주형 더미별 VIF입니다.')
            if (result['vif'].VIF > 5).any():
                st.warning('VIF 5 초과 항목이 있습니다. 작은 기준집단을 공유하는 부서 더미 간 상관도 포함되므로 계수의 불확실성과 기준집단을 함께 확인하세요.')
            for warning in result['warnings']:
                st.warning(warning)
    st.subheader('해석 가능한 의사결정나무')
    tree = results['tree']
    if 'error' in tree:
        st.error(tree['error'])
    else:
        st.caption('학습 70% / 검증 30%, 층화 분할, seed=42. 최대 깊이 3, 최소 리프 40명. 각 노드의 value=[재직, 퇴사]입니다.')
        fig, ax = plt.subplots(figsize=(22, 10))
        plot_tree(tree['model'], feature_names=tree['features'], class_names=['Stay', 'Leave'], filled=True, rounded=True, fontsize=8, ax=ax)
        st.pyplot(fig)
        plt.close(fig)
        st.write(f"학습 기준 퇴사율 {tree['train_base']:.1%} · 검증 기준 {tree['validation_base']:.1%}")
        st.dataframe(tree['rules'], width='stretch')
        st.caption('학습에서 찾은 규칙을 검증 집단에 적용했습니다. 작은 검증 리프는 불안정하며, 재현되지 않는 패턴은 정책 근거로 삼지 않습니다. 모든 규칙은 실제 적합한 트리에서 추출했습니다.')
        st.dataframe(tree['importance'], width='stretch')
        st.caption('불순도 감소 중요도는 분할 기여도입니다. 연속형 변수에 유리할 수 있고 상관된 변수 사이에 중요도가 분산됩니다. 인과적 중요도는 아닙니다.')

else:
    st.header('05 · HR Action')
    st.write('집단과 나머지 직원의 관찰 비율을 비교합니다. 30명 이상, 더 높은 관찰 퇴사율, 집단 비교 Fisher 검정의 Holm p<0.05를 모두 만족하면 우선 점검합니다. 정책 효과를 검증한 결과는 아닙니다.')
    action_table = results['actions']
    st.dataframe(action_table, width='stretch')
    for row in action_table.to_dict('records'):
        with st.container(border=True):
            st.subheader(f"{row['priority']} · {row['group']}")
            st.write(f"{row['n']}명 중 {row['leavers']}명 퇴사 · {row['rate']:.1%} · 나머지 대비 {row['difference_pp']:+.1f}%p · Holm p={row['p_holm']:.4g}")
            st.write('점검안: ' + row['policy'])
            st.caption('후속 측정: ' + row['follow_up_metric'])
    st.info('집단은 서로 겹칩니다. 인원수를 합산하거나 개인을 고위험자로 지정하지 않습니다. 급여 하위 집단은 동급 내 상대 기준일 뿐 저보상 판정이 아닙니다.')
    st.subheader('통계·모델 결과를 함께 읽기')
    logistic = results['logistic']
    if 'error' not in logistic:
        evidence = logistic['table']
        st.dataframe(evidence[(evidence.CI_low > 1) | (evidence.CI_high < 1)], width='stretch')
        st.caption('선택 변수를 통제한 탐색적 95% CI가 1을 포함하지 않는 요인입니다. 단변량 차이와 방향을 함께 확인하되, 이 표만으로 정책 우선순위를 확정하지 않습니다.')
    tree = results['tree']
    if 'error' not in tree:
        st.write('트리 규칙의 검증 집단 관찰 결과')
        st.dataframe(tree['rules'].query("split == 'validation'").drop(columns='split'), width='stretch')
        st.caption('학습 규칙은 검증 집단에서도 재현되는지 확인합니다. 작은 리프의 높은 비율만으로 정책 대상을 정하지 않습니다. 학습·검증 비교는 Attrition Drivers에서 볼 수 있습니다.')
    st.write('현장 맥락 확인 → 익명 설문·업무량 자료로 가설 보완 → 일부 조직에서 정책 시범 운영 → 비교 집단과 전후 추세로 유지율·만족도·업무부담 평가')
    st.caption('정책 시행 시점·퇴사 시점·추적 관측이 없어 정책 효과나 미래 연간 이탈률을 추정할 수 없습니다.')
