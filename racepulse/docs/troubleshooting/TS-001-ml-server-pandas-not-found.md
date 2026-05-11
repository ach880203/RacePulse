# TS-001 | ModuleNotFoundError: No module named 'pandas'

- **발생일:** 2026-05-11
- **서버:** FastAPI ML 서버 (포트 8000)
- **프롬프트:** 15-ml-model-training-prompt.md 실행 직후

---

## 에러 메시지

```
Process SpawnProcess-1:
...
ModuleNotFoundError: No module named 'pandas'
```

---

## 원인

`15-ml-model-training-prompt.md` 실행 시 `requirements.txt`에 패키지를 추가했지만,
`pip install`을 실제로 실행하지 않아서 venv에 설치가 안 된 상태였다.

**requirements.txt에는 있지만 venv에는 없었던 패키지:**
- `pandas>=2.2.0`
- `scikit-learn>=1.5.0`

---

## 진단 방법

```powershell
# 1. venv에 설치된 패키지 목록 확인
cd "c:\Programmer\Work\horse racing\racepulse\ml-server"
.\venv\Scripts\python.exe -m pip list | Select-String "pandas|numpy|scikit|xgboost|lightgbm|joblib"

# 2. 앱 전체 import 테스트
.\venv\Scripts\python.exe -c "from app.main import app; print('app import OK')"
```

---

## 해결 방법

```powershell
cd "c:\Programmer\Work\horse racing\racepulse\ml-server"

# 누락된 패키지 직접 설치
.\venv\Scripts\python.exe -m pip install "pandas>=2.2.0" "scikit-learn>=1.5.0"

# 설치 확인
.\venv\Scripts\python.exe -c "import pandas; import sklearn; print('OK - pandas:', pandas.__version__, '/ sklearn:', sklearn.__version__)"

# 앱 전체 import 테스트
.\venv\Scripts\python.exe -c "from app.main import app; print('app import OK')"
```

**설치 결과 (2026-05-11 기준):**
- pandas 3.0.2 ✅
- scikit-learn 1.8.0 ✅

---

## 예방책

새 프롬프트 실행 후 `requirements.txt`가 변경된 경우 반드시 아래 명령어를 실행할 것:

```powershell
cd "c:\Programmer\Work\horse racing\racepulse\ml-server"
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

---

## 참고: 현재 venv ML 관련 패키지 전체 목록

| 패키지 | 버전 |
|--------|------|
| numpy | 2.4.4 |
| pandas | 3.0.2 |
| scikit-learn | 1.8.0 |
| xgboost | 3.2.0 |
| lightgbm | 4.6.0 |
| joblib | 1.5.3 |
