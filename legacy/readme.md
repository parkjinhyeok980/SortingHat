# 그리핀도르 모자(Sorting Hat)

> **Sorting Hat, 통칭 그리핀도르 모자는 개인-환경 적합성(Person-Environment Fit) 이론을 기반으로 개인과 조직·직무 간의 적합성을 분석하여 알맞은 팀 조합을 추천해주는 HR Analytics 프로젝트입니다**


기업의 채용과 인력배치에서는 지원자의 역량뿐만 아니라 조직문화, 직무 특성, 개인의 가치관과 성향 등 다양한 요소가 함께 고려됩니다.
조직행동론에서는 이러한 관계를 **개인-환경 적합성(Person-Environment Fit, P-E Fit)**이라는 개념으로 설명합니다.

해당 프로젝트는 P-E Fit 이론을 기반으로,
MPPGF 척도를 활용하여 사원의 직위, 성향, 가치관, 업무태도에 관한 더미데이터를 생성한 뒤, 
어떤 조직원과 한 팀이 되었을 때 최대 업무효율 발휘 및 직무 만족도가 최상이 되는지를 분석하는 모델입니다.

## Windows 실행 환경

프로젝트 폴더에서 PowerShell로 실행합니다. 가상환경은 Git에 포함되지 않으므로 컴퓨터마다 한 번씩 생성해야 합니다.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

웹 화면 실행:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

브라우저에서 http://localhost:8501 에 접속합니다. 종료하려면 터미널에서 `Ctrl+C`를 누릅니다. 가상환경의 Python을 직접 사용하므로 별도 활성화나 PowerShell 실행 정책 변경은 필요하지 않습니다.

테스트 및 노트북 실행:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m jupyter lab
```

VS Code에서는 Python 인터프리터와 노트북 커널로 `.venv\Scripts\python.exe`를 선택합니다. 샘플 데이터(`data/employees_sample.csv`)와 화면 설정(`.streamlit/config.toml`)은 저장소에 포함되어 있으며, 별도 API 키나 `.env` 파일은 필요하지 않습니다. 생성 결과는 Git에서 제외되는 `outputs/` 폴더에 보관할 수 있습니다.
