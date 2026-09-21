"""Transparent project requirement matching, independent of personality scores."""

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


def analyze_project_candidates(teams, skills, roles, target=70) -> pd.DataFrame:
    """70% skill coverage + 30% distinct primary-role coverage.

    Each skill is covered by the strongest member, capped at its target.
    Availability is filtered before generation; it is not a quality score.
    """
    if not skills or not roles or not 0 < target <= 100:
        raise ValueError("필요 역량·역할과 1~100 사이의 목표 수준을 지정하세요.")
    if not set(skills) <= set(SKILLS) or not set(roles) <= set(ROLES):
        raise ValueError("지원하지 않는 역량 또는 역할입니다.")
    skills, roles = list(dict.fromkeys(skills)), list(dict.fromkeys(roles))
    rows = []
    for number, team in enumerate(teams, 1):
        maxima = team[skills].max()
        skill_score = float(np.minimum(maxima / target, 1).mean() * 100)
        covered_roles = set(team.role) & set(roles)
        role_score = len(covered_roles) / len(roles) * 100
        rows.append({
            "team_id": f"T{number:04d}", "member_ids": team.employee_id.tolist(),
            "member_names": team.name.tolist(), "fit_score": skill_score * .7 + role_score * .3,
            "skill_score": skill_score, "role_score": role_score,
            "minimum_availability": float(team.availability.min()),
            "missing_skills": [SKILLS[s] for s in skills if maxima[s] < target],
            "missing_roles": [r for r in roles if r not in covered_roles],
        })
    return pd.DataFrame(rows)
