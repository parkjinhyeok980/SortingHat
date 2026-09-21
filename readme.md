# 그리핀도르 모자(Sorting Hat)

## 웹 화면으로 실행하기 (Streamlit)

프로젝트 폴더의 PowerShell에서 최초 한 번 실행합니다.

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
```

이후 아래 명령으로 웹 화면을 실행합니다. 브라우저에서 `http://localhost:8501`에 접속하세요. 종료는 터미널에서 `Ctrl+C`입니다.

```powershell
.\.venv\Scripts\python -m streamlit run app.py
```

- 샘플 직원 20명으로 바로 시작하며, 같은 형식의 UTF-8 CSV를 업로드할 수 있습니다.
- 직원 성향 탭에서 직원을 선택하고, 숫자가 표시된 가로 막대로 개인 점수와 대상 직원 평균을 비교합니다.
- 왼쪽에서 부서, 팀 인원 또는 직급별 인원을 정하고 **팀 조합 분석하기**를 누릅니다.
- 팀 조합 비교 탭에서 유사성/다양성 순위, 팀 평균 레이더 차트, 팀원별 점수를 확인하고 전체 결과를 CSV로 내려받습니다.
- 조건을 변경하면 다시 분석해야 합니다. 화면 멈춤을 줄이기 위해 1회 분석은 최대 20,000개 조합으로 제한합니다.

후보 팀은 서로 직원을 공유할 수 있으며, 전체 직원을 겹치지 않게 배치한 결과는 아닙니다. 현재 유사성/다양성 점수는 성향의 거리 기반 지표이며 업무성과 예측이나 검증된 인사 추천 점수가 아닙니다.

### 이 프로젝트에 Streamlit을 쓰는 이유

현재 분석은 Python/pandas와 `src/` 함수로 구현되어 있습니다. Streamlit은 이 함수를 직접 호출하면서 입력 위젯과 차트를 웹에 표시하므로 노트북 셀 실행 없이 탐색하기에 적합합니다. Vue 3로도 구현할 수 있지만 기존 Python 분석을 연결할 API 서버와 프런트엔드 상태/차트 코드를 별도로 관리하는 구성이 보통 필요합니다. 세밀한 UI, 복잡한 화면 전환과 서비스 확장이 중심이 되면 Vue 3를 검토할 수 있습니다.

참고: [Streamlit 앱 만들기](https://docs.streamlit.io/get-started/tutorials/create-an-app), [Vue 소개](https://vuejs.org/guide/introduction).

기존 노트북과 `python main.py` 실행 방식도 사용할 수 있습니다.

> **Sorting Hat, 통칭 그리핀도르 모자는 개인-환경 적합성(Person-Environment Fit) 이론을 기반으로 개인과 조직·직무 간의 적합성을 분석하여 알맞은 팀 조합을 추천해주는 HR Analytics 프로젝트입니다**


기업의 채용과 인력배치에서는 지원자의 역량뿐만 아니라 조직문화, 직무 특성, 개인의 가치관과 성향 등 다양한 요소가 함께 고려됩니다.
조직행동론에서는 이러한 관계를 **개인-환경 적합성(Person-Environment Fit, P-E Fit)**이라는 개념으로 설명합니다.

해당 프로젝트는 P-E Fit 이론을 기반으로,
Big 5 이론을 활용하여 사원의 직위, 성향, 가치관, 업무태도에 관한 더미데이터를 생성한 뒤, 
어떤 조직원과 한 팀이 되었을 때 최대 업무효율 발휘 및 직무 만족도가 최상이 되는지를 분석하는 모델입니다.


![Sorting Hat 프로젝트 화면](<docsimg/스크린샷 2026-09-20 165509.png>)
