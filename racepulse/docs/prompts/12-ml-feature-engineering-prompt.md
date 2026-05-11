# 12. RacePulse ML 피처 엔지니어링 기초 프롬프트

> ⚠️ 이 프롬프트를 실행하기 전에 `docs/PROJECT_RULES.md` 파일을 먼저 읽고
> 모든 규칙을 준수하여 코드를 작성해주세요.

---

## 목표
수집된 경마 데이터를 ML 모델 학습에 사용할 수 있도록
피처(특징값)를 계산하고 ml_feature_store 테이블에 저장합니다.
XGBoost/LightGBM 모델 학습의 기반이 됩니다.

---

## 프로젝트 환경
- Python 3.13
- FastAPI 0.115.12
- SQLAlchemy 2.0 (async)
- pandas (데이터 처리)
- scikit-learn (피처 스케일링)
- PostgreSQL 16 + pgvector

---

## ML 피처 목록 (총 20개+)

### 말 관련 피처
```
horse_win_rate_total      ← 통산 승률
horse_win_rate_recent     ← 최근 1년 승률
horse_place_rate          ← 연대율 (2위 이내)
horse_weight              ← 마체중
horse_weight_diff         ← 마체중 증감
days_since_last_race      ← 직전 경주로부터 경과일
avg_rank_last5            ← 최근 5경주 평균 착순
best_rank_last5           ← 최근 5경주 최고 착순
distance_win_rate         ← 해당 거리에서의 승률
course_win_rate           ← 해당 경마장에서의 승률
condition_win_rate        ← 해당 트랙 상태에서의 승률
is_debut                  ← 데뷔전 여부 (0/1)
is_comeback               ← 장기 결장 후 복귀 여부 (0/1)
class_change              ← 클래스 변동 (-1/0/1)
```

### 기수 관련 피처
```
jockey_win_rate_total     ← 기수 통산 승률
jockey_win_rate_recent    ← 기수 최근 승률
jockey_horse_win_rate     ← 이 기수+이 말 조합 승률
```

### 조교사 관련 피처
```
trainer_win_rate_total    ← 조교사 통산 승률
trainer_horse_win_rate    ← 이 조교사+이 말 조합 승률
```

### 경주 조건 피처
```
gate_win_rate             ← 해당 경마장/거리에서 이 게이트 승률
burden_weight             ← 부담중량
odds_win                  ← 단승 배당률 (낮을수록 강함)
```

---

## 구현 파일 목록

### 1. 피처 계산 서비스
`app/services/feature_engineering.py`

구현 메서드:
- `calculate_horse_features(horse_id, race_id)` → 말 관련 피처 계산
- `calculate_jockey_features(jockey_id, horse_id)` → 기수 관련 피처 계산
- `calculate_race_features(race_entry_id)` → 경주 조건 피처 계산
- `build_feature_vector(race_entry_id)` → 전체 피처 벡터 생성
- `save_to_feature_store(race_entry_id, features)` → ml_feature_store 저장

### 2. 피처 스토어 모델
`app/models/ml.py`
- `MLFeatureStore` 클래스 → ml_feature_store 테이블
- `Prediction` 클래스 → predictions 테이블
- `ModelVersion` 클래스 → model_versions 테이블

### 3. 배치 피처 계산
`app/services/feature_batch.py`
- `calculate_all_features_for_race(race_id)` → 특정 경주 전체 출전마 피처 계산
- `recalculate_historical_features(start_date, end_date)` → 과거 데이터 일괄 계산

### 4. API 엔드포인트
`app/api/ml.py`
- `POST /ml/features/calculate/{race_id}` → 특정 경주 피처 계산 트리거
- `GET /ml/features/{race_entry_id}` → 저장된 피처 조회

---

## 주석 요구사항 ⚠️ 반드시 지켜주세요

이 프로젝트의 개발자는 **코딩 입문자**입니다.
**학생을 가르친다는 생각**으로 모든 코드에 한국어 주석을 달아주세요.

- 피처(Feature)가 ML에서 무엇을 의미하는지 설명
- 피처 벡터가 무엇인지 설명 (숫자 배열로 변환하는 이유)
- 승률 계산 공식 설명
- 왜 피처를 미리 계산해서 저장하는지 설명 (성능 이유)
- pandas DataFrame 기본 개념 설명

---

## 인코딩 주의사항 ⚠️
- 모든 파일은 **UTF-8 (BOM 없음)** 으로 저장
- Python 파일 최상단: `# -*- coding: utf-8 -*-`
- 한글 주석이 깨지지 않도록 확인

---

## 완료 기준
1. `POST http://localhost:8000/ml/features/calculate/1` 실행 시 피처 계산 성공
2. `ml_feature_store` 테이블에 JSONB 형태로 피처 저장 확인
3. `GET http://localhost:8000/ml/features/1` 피처 조회 성공
4. 20개 이상의 피처가 계산됨 확인
