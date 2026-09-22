"""Transparent project requirement matching, independent of survey responses."""

from io import BytesIO

import numpy as np
import pandas as pd

SKILLS = {"planning": "기획", "design": "디자인", "engineering": "개발", "analytics": "데이터 분석", "operations": "운영"}
ROLES = ["기획", "디자인", "개발", "데이터 분석", "운영"]
PRESETS = {
    "신규 서비스 출시": {"skills": ["planning", "design", "engineering"], "roles": ["기획", "디자인", "개발"]},
    "데이터 기반 개선": {"skills": ["planning", "analytics", "engineering"], "roles": ["기획", "데이터 분석", "개발"]},
    "운영 프로세스 개선": {"skills": ["planning", "analytics", "operations"], "roles": ["기획", "데이터 분석", "운영"]},
}
BASE_COLUMNS = ["employee_id", "name", "rank", "current_department", "role"]


def read_project_data(raw: bytes) -> pd.DataFrame:
    frame = pd.read_csv(BytesIO(raw), dtype={column: str for column in BASE_COLUMNS})
    required = BASE_COLUMNS + list(SKILLS) + ["availability"]
    missing = set(required) - set(frame.columns)
    if missing:
        raise ValueError(f"필수 열이 없습니다: {', '.join(sorted(missing))}")
    for column in BASE_COLUMNS:
        frame[column] = frame[column].str.strip()
        if frame[column].isna().any() or frame[column].eq("").any():
            raise ValueError(f"{column}에 빈 값이 있습니다.")
    if frame.employee_id.duplicated().any():
        raise ValueError("직원 ID는 중복될 수 없습니다.")
    if not frame.role.isin(ROLES).all():
        raise ValueError(f"role은 다음 중 하나여야 합니다: {', '.join(ROLES)}")
    for column in list(SKILLS) + ["availability"]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
        if not frame[column].between(0, 100).all():
            raise ValueError(f"{column}은 0~100 사이의 숫자여야 합니다.")
    return frame.reset_index(drop=True)


def complementarity_score(values, target):
    """Maximum distinct-member assignment coverage; one specialty per member."""
    coverage = np.minimum(values / target, 1)
    scores = {0: 0.0}
    for member in coverage:
        updated = dict(scores)
        for mask, score in scores.items():
            for skill, value in enumerate(member):
                if not mask & (1 << skill):
                    next_mask = mask | (1 << skill)
                    updated[next_mask] = max(updated.get(next_mask, 0), score + float(value))
        scores = updated
    return max(scores.values()) / values.shape[1] * 100


def knowledge_sharing(team, skills, target):
    """One strongest mentor per learner/skill, normalized for team size."""
    values = team[list(SKILLS)].to_numpy(dtype=float)
    ranks = team[list(SKILLS)].rank(axis=1, method="min", ascending=False).to_numpy()
    links = []
    credit = 0.0
    for skill in skills:
        col = list(SKILLS).index(skill)
        mentor = int(np.argmax(values[:, col]))
        expert = values[mentor, col]
        if expert < target:
            continue
        for learner, level in enumerate(values[:, col]):
            eligible = (ranks[learner, col] == 2 and level >= target * .5) or level >= target * .8
            if learner == mentor or level >= expert or not eligible:
                continue
            credit += min(level / target, 1)
            teacher, student = team.iloc[mentor], team.iloc[learner]
            links.append(f"{SKILLS[skill]}: {teacher['name']} ({teacher.employee_id}, {expert:g}) → {student['name']} ({student.employee_id}, {level:g})")
    denominator = max(len(team) - 1, 1) * len(skills)
    return 10 * credit / denominator, links


def rank_project_candidates(results):
    """Complementarity always wins; sharing refines equal-coverage teams."""
    return results.sort_values(["complementarity_score", "fit_score", "skill_score", "role_score"], ascending=False, kind="stable")


def analyze_project_candidates(teams, skills, roles, target=70) -> pd.DataFrame:
    """Distinct-member coverage first, then level/role score + sharing bonus."""
    if not skills or not roles or not 0 < target <= 100:
        raise ValueError("필요 역량·역할과 1~100 사이의 목표 수준을 지정하세요.")
    if not set(skills) <= set(SKILLS) or not set(roles) <= set(ROLES):
        raise ValueError("지원하지 않는 역량 또는 역할입니다.")
    skills, roles = list(dict.fromkeys(skills)), list(dict.fromkeys(roles))
    rows = []
    for number, team in enumerate(teams, 1):
        if team.empty:
            raise ValueError("팀에는 최소 한 명의 구성원이 필요합니다.")
        maxima = team[skills].max()
        skill_score = float(np.minimum(maxima / target, 1).mean() * 100)
        covered_roles = set(team.role) & set(roles)
        role_score = len(covered_roles) / len(roles) * 100
        complementarity = complementarity_score(team[skills].to_numpy(dtype=float), target)
        bonus, links = knowledge_sharing(team, skills, target)
        rows.append({
            "team_id": f"T{number:04d}", "member_ids": team.employee_id.tolist(),
            "member_names": team.name.tolist(),
            "complementarity_score": round(complementarity, 8),
            "fit_score": skill_score * .7 + role_score * .3 + bonus,
            "sharing_bonus": bonus, "sharing_links": links,
            "skill_score": skill_score, "role_score": role_score,
            "minimum_availability": float(team.availability.min()),
            "missing_skills": [SKILLS[s] for s in skills if maxima[s] < target],
            "missing_roles": [r for r in roles if r not in covered_roles],
        })
    return pd.DataFrame(rows)
