# 15. RacePulse ML 모델 학습 프롬프트 (XGBoost/LightGBM)

> ⚠️ 이 프롬프트를 실행하기 전에 `docs/PROJECT_RULES.md` 파일을 먼저 읽고
> 모든 규칙을 준수하여 코드를 작성해주세요.

---

## 목표
12번 프롬프트로 계산된 피처 데이터를 이용해
XGBoost / LightGBM 모델을 학습하고 경주 결과를 예측합니다.
학습된 모델을 저장하고 FastAPI로 예측 API를 제공합니다.

---

## 프로젝트 환경
- Python 3.13
- FastAPI 0.115.12
- XGBoost, LightGBM, scikit-learn
- pandas, numpy
- joblib (모델 직렬화)
- PostgreSQL (ml_feature_store, predictions, model_versions)

---

## 현재 파일 구조
```
ml-server/app/
├── models/
│   └── ml.py              ← MLFeatureStore, Prediction, ModelVersion
├── services/
│   └── feature_engineering.py  ← 피처 계산 (12번)
└── api/
    └── ml.py              ← 피처 API (12번)
```

---

## 구현 파일 목록

### 1. 데이터 준비 서비스
`app/services/ml_dataset.py`

구현 메서드:
- `load_training_data(start_date, end_date)` → 학습 데이터 로드
  - ml_feature_store에서 피처 벡터 조회
  - race_results에서 실제 착순 조회
  - 학습용 X(피처), y(착순) 준비
- `split_train_test(X, y, test_size=0.2)` → 학습/테스트 분리
- `preprocess_features(X)` → 결측값 처리, 스케일링

### 2. 모델 학습 서비스
`app/services/ml_trainer.py`

구현 메서드:
- `train_xgboost(X_train, y_train)` → XGBoost 모델 학습
- `train_lightgbm(X_train, y_train)` → LightGBM 모델 학습
- `evaluate_model(model, X_test, y_test)` → 모델 평가
  - Top-1 정확도 (1위 예측 적중률)
  - Top-3 정확도 (3위 이내 예측 적중률)
- `save_model(model, model_name)` → 모델 파일 저장 (joblib)
- `load_model(model_name)` → 모델 파일 로드

### 3. 예측 서비스
`app/services/predictor.py`

구현 메서드:
- `predict_race(race_id)` → 특정 경주 예측
  - ml_feature_store에서 피처 로드
  - 학습된 모델로 각 말의 승률 계산
  - predictions 테이블에 저장
- `get_prediction_result(race_id)` → 예측 결과 조회
- `update_accuracy(race_id)` → 경기 결과 나온 후 정확도 업데이트

### 4. 모델 버전 관리
`app/services/model_manager.py`

구현 메서드:
- `register_model(model_info)` → model_versions 테이블에 저장
- `get_active_model()` → 현재 사용 중인 모델 조회
- `switch_model(model_version_id)` → 모델 교체

### 5. API 엔드포인트
`app/api/ml.py` 에 추가:
```
POST /ml/train                    ← 모델 학습 시작
GET  /ml/models                   ← 학습된 모델 목록
POST /ml/predict/{race_id}        ← 특정 경주 예측 실행
GET  /ml/accuracy                 ← 전체 정확도 현황
```

---

## 모델 설정값

### XGBoost 기본 파라미터
```python
xgb_params = {
    'objective': 'rank:pairwise',  # 순위 예측
    'max_depth': 6,
    'learning_rate': 0.1,
    'n_estimators': 300,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
}
```

### LightGBM 기본 파라미터
```python
lgb_params = {
    'objective': 'rank',
    'num_leaves': 31,
    'learning_rate': 0.1,
    'n_estimators': 300,
    'subsample': 0.8,
}
```

---

## 정확도 기준
```
Top-3 정확도 60% 미만 → 피처 재검토 필요
Top-3 정확도 70% 이상 → Phase 2 진행 기준 충족
```

---

## 주석 요구사항 ⚠️ 반드시 지켜주세요

이 프로젝트의 개발자는 **코딩 입문자**입니다.
**학생을 가르친다는 생각**으로 모든 코드에 한국어 주석을 달아주세요.

- XGBoost와 LightGBM이 무엇인지, 어떤 차이가 있는지 설명
- 학습(train)과 테스트(test) 분리가 왜 필요한지 설명
- Top-1 / Top-3 정확도 계산 방법 설명
- joblib으로 모델 저장/로드하는 이유 설명
- 과적합(overfitting)이 무엇인지 설명

---

## 인코딩 주의사항 ⚠️
- 모든 파일은 **UTF-8 (BOM 없음)** 으로 저장
- Python 파일 최상단: `# -*- coding: utf-8 -*-`
- 한글 주석이 깨지지 않도록 확인

---

## 완료 기준
1. `POST http://localhost:8000/ml/train` 모델 학습 성공
2. `model_versions` 테이블에 학습 결과 저장 확인
3. `POST http://localhost:8000/ml/predict/1` 예측 결과 생성
4. `predictions` 테이블에 각 말별 승률 저장 확인
5. Top-1 / Top-3 정확도 수치 출력 확인
