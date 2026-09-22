"""Reproducible fictional employees: python -m src.sample_data."""
import random
import pandas as pd
from src.config import SAMPLE_EMPLOYEES_CSV, PREFERENCE_COLUMNS, PERCEIVED_COLUMNS
from src.project_fit import SKILLS, ROLES


def generate_sample(seed=20260922):
    rng = random.Random(seed)
    rows = []
    team_profiles = {f"G{i+1:02d}": [rng.randint(1, 5) for _ in PREFERENCE_COLUMNS] for i in range(4)}
    for i in range(20):
        team_id = f"G{i % 4 + 1:02d}"
        row = {"employee_id": f"E{i+1:03d}", "name": f"가상직원{i+1:02d}",
               "rank": "팀장" if i < 4 else "과장" if i < 8 else "대리" if i < 14 else "사원",
               "current_department": ["제품", "서비스", "데이터", "운영"][i % 4],
               "current_team_id": team_id, "role": ROLES[i % 5], "availability": rng.choice([40, 60, 80, 100])}
        for j, skill in enumerate(SKILLS):
            row[skill] = rng.randint(80, 96) if j == i % 5 else rng.randint(52, 76) if j == (i+1) % 5 else rng.randint(20, 60)
        for j, item in enumerate(PREFERENCE_COLUMNS):
            row[item] = rng.randint(1, 5)
            row[f"observed_{item}"] = max(1, min(5, team_profiles[team_id][j] + rng.choice([-1, 0, 0, 1])))
        for item in PERCEIVED_COLUMNS:
            row[item] = rng.randint(1, 5)
        row["survey_example"] = ["중간 공유를 더 자주 원하지만 현재는 마감 때 공유한다.", "현재 팀의 사전 계획 방식이 내 선호와 비슷하다.", "동료와 서로 다른 전문 분야를 설명하며 작업했다.", "의사결정 자율성과 지원 범위를 다음 회의에서 논의하고 싶다."][i % 4]
        rows.append(row)
    return pd.DataFrame(rows)


if __name__ == "__main__":
    generate_sample().to_csv(SAMPLE_EMPLOYEES_CSV, index=False, encoding="utf-8")
