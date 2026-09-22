"""Competencies and custom Person–Group Fit survey schema."""
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
SAMPLE_EMPLOYEES_CSV = DATA_DIR / "employees_sample.csv"
EMPLOYEE_ID_COLUMN = "employee_id"
NAME_COLUMN = "name"
RANK_COLUMN = "rank"
DEPARTMENT_COLUMN = "current_department"
PREFERENCE_ITEMS = {
    "value_quality": ("가치관 · 완성도", "빠른 실행 우선", "충분한 검토·완성도 우선"),
    "goal_learning": ("목표 · 학습", "당장의 성과 우선", "장기적 학습·성장 우선"),
    "interest_innovation": ("관심사 · 새로운 시도", "기존 방식 개선", "새로운 방식 탐색"),
    "work_planning": ("업무 방식 · 계획", "상황에 따른 유연한 진행", "사전 계획에 따른 진행"),
    "communication_frequency": ("업무 방식 · 진행 공유", "주요 이정표 때 공유", "작은 진행도 자주 공유"),
    "feedback_frequency": ("필요 · 피드백", "완료 후 피드백", "진행 중 수시 피드백"),
    "autonomy_need": ("필요 · 자율성", "구체적인 지시 선호", "독립적인 결정 선호"),
    "support_need": ("필요 · 지원", "혼자 해결하는 방식 선호", "함께 해결하는 지원 선호"),
}
PERCEIVED_ITEMS = {
    "perceived_values": ("가치관", "나와 현재 팀은 일에서 중요하게 여기는 기준이 비슷하다."),
    "perceived_goals": ("목표", "내가 달성하고 싶은 결과와 현재 팀이 추구하는 결과가 잘 맞는다."),
    "perceived_workstyle": ("업무 방식", "현재 팀의 계획·속도·소통 방식이 나와 잘 맞는다."),
    "perceived_needs": ("필요 충족", "현재 팀은 내가 일하는 데 필요한 지원과 자율성을 제공한다."),
    "perceived_complementarity": ("상호보완성", "내 강점은 현재 팀에 부족한 부분을 채워준다."),
}
PREFERENCE_COLUMNS = list(PREFERENCE_ITEMS)
PERCEIVED_COLUMNS = list(PERCEIVED_ITEMS)
OBSERVED_COLUMNS = [f"observed_{c}" for c in PREFERENCE_COLUMNS]
SURVEY_COLUMNS = PREFERENCE_COLUMNS + OBSERVED_COLUMNS + PERCEIVED_COLUMNS
REQUIRED_COLUMNS = [EMPLOYEE_ID_COLUMN, NAME_COLUMN, RANK_COLUMN, DEPARTMENT_COLUMN, "current_team_id", *SURVEY_COLUMNS]
