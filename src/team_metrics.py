"""Item-level preference comparisons, not a validated PG-fit score."""
import pandas as pd
from src.config import PREFERENCE_ITEMS


def analyze_team(team):
    if team.empty:
        raise ValueError("팀에는 최소 한 명이 필요합니다.")
    result = {"member_ids": team.employee_id.tolist(), "member_names": team.name.tolist()}
    for item in PREFERENCE_ITEMS:
        result[f"{item}_mean"] = float(team[item].mean())
        result[f"{item}_range"] = float(team[item].max() - team[item].min())
    return result


def compare_member_preferences(team):
    """Exclude the person from the peer mean; preserve signed differences."""
    rows = []
    for _, person in team.iterrows():
        peers = team[team.employee_id != person.employee_id]
        for item, (label, _, _) in PREFERENCE_ITEMS.items():
            peer_mean = float(peers[item].mean()) if len(peers) else None
            rows.append({"직원": f"{person['name']} · {person.employee_id}", "항목": label,
                         "본인 선호": float(person[item]), "다른 팀원 평균": peer_mean,
                         "차이 (본인−동료)": float(person[item]) - peer_mean if peer_mean is not None else None})
    return pd.DataFrame(rows)
