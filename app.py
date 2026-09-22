"""Interactive Big Five team explorer: python -m streamlit run app.py."""

from math import comb, prod
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from src.config import BIG5_COLUMNS, SAMPLE_EMPLOYEES_CSV
from src.data_loader import validate_employees
from src.simulator import analyze_team_candidates
from src.project_fit import SKILLS, ROLES, PRESETS, read_project_data, analyze_project_candidates, rank_project_candidates
from src.team_generator import generate_teams, generate_teams_with_rank_constraints


LABELS = dict(zip(BIG5_COLUMNS, ["외향성", "우호성", "성실성", "개방성", "정서적 안정성"]))
LABELS.update(SKILLS)
LABELS.update(role="담당 역할", availability="투입 가능률")
LABELS.update(employee_id="직원 ID", name="이름", rank="직급", current_department="부서")
LIMIT = 20_000


def read_data(raw: bytes) -> pd.DataFrame:
    employees = read_project_data(raw)
    for column in BIG5_COLUMNS:
        if column in employees:
            employees[column] = pd.to_numeric(employees[column], errors="coerce")
    validate_employees(employees)
    return employees.reset_index(drop=True)


def main() -> None:
    st.set_page_config(page_title="Sorting Hat · 팀 역량·성향 탐색", page_icon="🎩", layout="wide")
    st.html(f"<style>{(Path(__file__).parent / 'assets/style.css').read_text(encoding='utf-8')}</style>")
    st.html('''<div class="topline"><span>Workspace &nbsp; / &nbsp; 팀 구성 스튜디오</span><span class="badge">TEAM EXPLORER</span></div>
    <div class="hero"><div class="eyebrow">BETTER TOGETHER, BY DESIGN</div>
    <h1>좋은 팀의 시작,<br>서로를 이해하는 것부터.</h1>
    <p>구성원의 특성을 살펴보고, 함께할 때의 가능성을 발견하세요.<br>팀 구성 조건부터 후보 비교까지, 한곳에서.</p>
    <div class="orbit" aria-hidden="true"><i></i><i></i><i></i></div></div>''')

    with st.sidebar:
        st.html('<div class="brand"><span class="brand-mark">✳</span> Sorting Hat</div><div class="brand-sub">TEAM DESIGN STUDIO</div>')
        st.subheader("01 / 구성원 데이터")
        upload = st.file_uploader("직원 CSV 업로드", type=["csv"])
        st.caption("업로드하지 않으면 샘플 직원 20명을 사용합니다. 점수 범위는 0~100입니다.")
        st.download_button("샘플 CSV 다운로드", SAMPLE_EMPLOYEES_CSV.read_bytes(), "employees_sample.csv", "text/csv")
    try:
        raw = upload.getvalue() if upload is not None else SAMPLE_EMPLOYEES_CSV.read_bytes()
        employees = read_data(raw)
    except (ValueError, TypeError, UnicodeError, pd.errors.ParserError) as exc:
        st.error(f"CSV를 확인해 주세요: {exc}")
        st.info("샘플 CSV의 열 이름을 유지하고, 빈 값·중복 ID·숫자가 아닌 역량·성향 점수를 확인해 주세요. UTF-8 CSV를 사용하세요.")
        return
    if len(employees) < 2:
        st.warning("팀 비교에는 직원이 최소 2명 필요합니다.")
        return

    with st.sidebar:
        departments = st.multiselect("분석 대상 부서", employees.current_department.unique().tolist(), default=employees.current_department.unique().tolist())
    pool = employees[employees.current_department.isin(departments)].reset_index(drop=True)
    if len(pool) < 2:
        st.info("분석 대상 부서를 선택해 직원을 2명 이상 포함해 주세요.")
        return
    with st.sidebar:
        st.subheader("02 / 팀 구성 조건")
        constrained = st.checkbox("직급별 인원 지정")
        constraints = None
        if constrained:
            constraints = {
                rank: int(st.number_input(f"{rank} 인원", min_value=0, max_value=int(count), value=1, step=1))
                for rank, count in pool['rank'].value_counts().items()
            }
            team_size = sum(constraints.values())
            candidate_count = prod(comb(int((pool['rank'] == rank).sum()), count) for rank, count in constraints.items())
            st.write(f"팀당 {team_size}명")
        else:
            team_size = int(st.number_input("팀당 인원", min_value=2, max_value=len(pool), value=min(5, len(pool)), step=1))
            candidate_count = comb(len(pool), team_size)
        st.metric("가능한 팀 조합", f"{candidate_count:,}개")
        valid = team_size >= 2 and candidate_count <= LIMIT
        if team_size < 2:
            st.warning("팀 인원을 2명 이상 지정해 주세요.")
        if candidate_count > LIMIT:
            st.warning(f"한 번에 {LIMIT:,}개까지 분석합니다. 부서나 직급 조건을 좁혀 주세요.")
        st.subheader("03 / 프로젝트 요구사항")
        preset = st.selectbox("프로젝트 유형", list(PRESETS))
        required_skills = st.multiselect("필요 역량", list(SKILLS), default=PRESETS[preset]["skills"], format_func=SKILLS.get, key=f"skills_{preset}")
        required_roles = st.multiselect("필요 역할", ROLES, default=PRESETS[preset]["roles"], key=f"roles_{preset}")
        target = st.slider("역량 목표 수준", 1, 100, 70)
        valid = valid and bool(required_skills) and bool(required_roles)
        if not required_skills or not required_roles:
            st.warning("필요 역량과 역할을 각각 하나 이상 선택해 주세요.")
        run = st.button("팀 조합 분석하기", type="primary", disabled=not valid, use_container_width=True)

    overview, results_tab = st.tabs(["직원 역량·성향 둘러보기", "팀 조합 비교"])
    with overview:
        cols = st.columns(3)
        cols[0].metric("분석 대상", f"{len(pool)}명")
        cols[1].metric("부서", f"{pool.current_department.nunique()}개")
        cols[2].metric("팀당 인원", f"{team_size}명")
        st.subheader("직원 프로필")
        person = st.selectbox("직원 선택", pool.index.tolist(), format_func=lambda i: f"{pool.loc[i, 'name']} · {pool.loc[i, 'employee_id']}")
        st.caption(f"담당 역할: {pool.loc[person, 'role']} · 투입 가능률: {pool.loc[person, 'availability']:.0f}%")
        skills_profile = pd.DataFrame({"역량": list(SKILLS.values()), "선택 직원": pool.loc[person, list(SKILLS)].astype(float).tolist(), "대상 직원 평균": pool[list(SKILLS)].mean().tolist()})
        st.plotly_chart(px.bar(skills_profile.melt(id_vars="역량", var_name="구분", value_name="점수"), x="역량", y="점수", color="구분", barmode="group", range_y=[0, 100], title="업무 역량"), use_container_width=True)
        st.subheader("Big Five 성향")
        profile = pd.DataFrame({"성향": list(LABELS[c] for c in BIG5_COLUMNS), "선택 직원": pool.loc[person, BIG5_COLUMNS].astype(float).tolist(), "대상 직원 평균": pool[BIG5_COLUMNS].mean().tolist()})
        fig = px.bar(
            profile.melt(id_vars="성향", var_name="구분", value_name="점수"),
            x="점수", y="성향", color="구분", orientation="h",
            barmode="group", range_x=[0, 110], text="점수",
            color_discrete_map={"선택 직원": "#2563EB", "대상 직원 평균": "#94A3B8"},
        )
        fig.update_traces(texttemplate="%{x:.1f}", textposition="outside", cliponaxis=False)
        fig.update_layout(height=430, yaxis=dict(autorange="reversed"), xaxis=dict(tickvals=[0, 20, 40, 60, 80, 100]), legend=dict(orientation="h", y=1.12))
        st.plotly_chart(fig, use_container_width=True)
        st.caption("막대 길이와 숫자로 비교하세요. 대상 직원 평균은 현재 선택한 부서 기준이며, 이상적인 성향 점수를 뜻하지 않습니다.")
        with st.expander("원본 데이터 확인"):
            st.dataframe(pool.rename(columns=LABELS), hide_index=True, use_container_width=True)

    # Bind results to their exact input so changed controls never show stale rankings.
    signature = ("complementarity-v2", raw, tuple(departments), team_size, tuple(constraints.items()) if constraints else None, tuple(required_skills), tuple(required_roles), target)
    if st.session_state.get("analysis_signature") != signature:
        st.session_state.pop("analysis_results", None)
    if run and valid:
        with st.spinner(f"{candidate_count:,}개 팀의 역량과 성향을 분석하고 있습니다…"):
            teams = generate_teams_with_rank_constraints(pool, constraints) if constraints else generate_teams(pool, team_size)
            teams = list(teams)
            personality = analyze_team_candidates(teams)
            competencies = analyze_project_candidates(teams, required_skills, required_roles, target)
            st.session_state.analysis_results = personality.merge(competencies.drop(columns=["member_ids", "member_names"]), on="team_id", validate="one_to_one")
            st.session_state.analysis_signature = signature

    with results_tab:
        if "analysis_results" not in st.session_state:
            st.info("왼쪽에서 조건을 설정하고 ‘팀 조합 분석하기’를 누르면 순위와 상세 비교가 표시됩니다.")
            return
        results = st.session_state.analysis_results
        st.success(f"{len(results):,}개 조합 분석 완료")
        st.caption("각 행은 독립적인 팀 후보입니다. 서로 다른 후보에 같은 직원이 포함될 수 있습니다.")
        order = st.radio("어떤 팀부터 볼까요?", ["업무역량 상호 보완 우선", "성향이 비슷한 팀", "성향이 다양한 팀"], horizontal=True)
        score = {"업무역량 상호 보완 우선": "fit_score", "성향이 비슷한 팀": "personality_similarity_score", "성향이 다양한 팀": "personality_diversity_score"}[order]
        ranked = rank_project_candidates(results) if order == "업무역량 상호 보완 우선" else results.sort_values(score, ascending=False, kind="stable")
        top_n = st.select_slider("상위 후보 수", options=[5, 10, 20], value=5)
        top = ranked.head(top_n)
        table = top[["team_id", "member_names", "complementarity_score", "sharing_bonus", "fit_score", "skill_score", "role_score", "personality_similarity_score", "personality_diversity_score"]].copy()
        table['member_names'] = table.member_names.apply(lambda names: ", ".join(map(str, names)))
        table.columns = ["팀 ID", "구성원", "상호 보완성", "공유 보너스", "수준·공유 점수", "역량 충족도", "역할 충족도", "유사성 지표", "다양성 지표"]
        st.dataframe(table, hide_index=True, use_container_width=True)
        st.subheader("선택한 팀 자세히 보기")
        selected = st.selectbox("팀 후보 선택", top.team_id.tolist())
        row = results.set_index("team_id").loc[selected]
        members = pool[pool.employee_id.isin(row.member_ids)]
        fit_cols = st.columns(5)
        fit_cols[0].metric("수준·공유 점수 / 110", f"{row.fit_score:.1f}")
        fit_cols[3].metric("상호 보완성 / 100", f"{row.complementarity_score:.1f}")
        fit_cols[4].metric("공유 보너스 / 10", f"{row.sharing_bonus:.2f}")
        fit_cols[1].metric("역량 충족도 / 100", f"{row.skill_score:.1f}")
        fit_cols[2].metric("역할 충족도 / 100", f"{row.role_score:.1f}")
        st.caption(f"목표 미달 역량: {', '.join(row.missing_skills) or '없음'} · 미충족 역할: {', '.join(row.missing_roles) or '없음'} · 팀 내 최소 투입 가능률: {row.minimum_availability:.0f}%")
        with st.expander("지식 공유 보너스 근거"):
            if row.sharing_links:
                for link in row.sharing_links:
                    st.write(link)
            else:
                st.write("현재 기준을 충족하는 공유 연결이 없습니다.")
        coverage = pd.DataFrame({"역량": [SKILLS[c] for c in required_skills], "팀 내 최고 점수": members[required_skills].max().tolist(), "팀 평균": members[required_skills].mean().tolist()})
        figure = px.bar(coverage.melt(id_vars="역량", var_name="구분", value_name="점수"), x="역량", y="점수", color="구분", barmode="group", range_y=[0, 100], title="프로젝트 필요 역량")
        figure.add_hline(y=target, line_dash="dash", annotation_text=f"목표 {target}")
        st.plotly_chart(figure, use_container_width=True)
        cols = st.columns(2)
        cols[0].metric("유사성 지표 · 0~1", f"{row.personality_similarity_score:.4f}")
        cols[1].metric("다양성 지표 · 평균 거리", f"{row.personality_diversity_score:.2f}")
        profile = pd.DataFrame({"성향": [LABELS[c] for c in BIG5_COLUMNS], "선택 팀": [row[f'{c}_mean'] for c in BIG5_COLUMNS], "대상 직원 평균": pool[BIG5_COLUMNS].mean().tolist()})
        st.plotly_chart(px.line_polar(profile.melt(id_vars="성향", var_name="구분", value_name="점수"), r="점수", theta="성향", color="구분", line_close=True, range_r=[0, 100]), use_container_width=True)
        st.dataframe(members.rename(columns=LABELS), hide_index=True, use_container_width=True)
        spread = members.assign(직원=members['name'].astype(str) + ' · ' + members.employee_id.astype(str)).melt(id_vars="직원", value_vars=BIG5_COLUMNS, var_name="성향", value_name="점수")
        spread['성향'] = spread['성향'].map(LABELS)
        st.plotly_chart(px.bar(spread, x="성향", y="점수", color="직원", barmode="group", range_y=[0, 100], title="팀원 간 성향 차이"), use_container_width=True)
        with st.expander("지표는 어떻게 읽나요?"):
            st.write("역량 충족도는 필요 역량별 팀 내 최고 점수를 목표 수준으로 나눈 값(최대 100%)의 평균입니다. 역할 충족도는 필요한 역할 중 담당자가 있는 비율입니다. 기본 정렬은 상호 보완성을 최우선으로 합니다. 각 팀원이 필요 역량 하나씩을 나눠 맡는 최적 배치에서 목표 충족률의 평균을 계산하며, 맡을 사람이 없는 역량은 0점입니다. 보완성이 같으면 역량 70% + 역할 30% + 공유 보너스(최대 10점)로 정렬합니다. 공유 보너스는 전체 5개 역량 중 공동 2위(경쟁 순위)이면서 목표의 50% 이상이거나, 목표의 80% 이상인 역량에 대해 목표 이상이며 자신보다 점수가 높은 동료가 있을 때 부여합니다. 역량별 최고점 동료 한 명만 연결하고, 연결별 min(본인 점수/목표, 1)의 합을 (팀원 수−1) × 필요 역량 수로 나눠 10을 곱합니다. 동점 최고점자는 데이터 순서상 첫 사람을 표시합니다. 공유 가능성은 점수 기반 가정입니다. 성향은 별도 참고자료로 함께 표시하며 성과 예측 점수가 아닙니다. 투입 가능률은 참고값이며 후보 제외 조건은 아닙니다.")
            st.write("다양성은 팀원 모든 쌍의 Big Five 유클리드 거리 평균입니다. 높을수록 성향이 넓게 분포합니다. 유사성은 1 / (1 + 다양성)으로 계산하며, 높을수록 성향이 가깝습니다. 두 값은 같은 거리에서 나온 반대 방향 지표로, 독립적인 평가 점수가 아닙니다.")
        export = ranked.copy()
        for column in ["member_ids", "member_names", "missing_skills", "missing_roles", "sharing_links"]:
            export[column] = export[column].apply(lambda values: ", ".join(map(str, values)))
        st.download_button("전체 분석 결과 CSV 다운로드", export.to_csv(index=False).encode("utf-8-sig"), "team_analysis.csv", "text/csv")


if __name__ == "__main__":
    main()
