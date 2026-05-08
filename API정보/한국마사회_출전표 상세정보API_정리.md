# 한국마사회 API 파일 비교 정리

## 1. 비교 대상

| 구분 | 파일 | 설명 |
|---|---|---|
| 파일 A | 붙여넣은 XML 응답 샘플 | 실제 `<item>` 데이터 10건 기준 |
| 파일 B | `API26_2_한국마사회 출전표 상세정보.docx` | 한국마사회 출전표 상세정보 API 명세 문서 |

---

## 2. 한 줄 결론

두 파일은 같은 경마 데이터 계열이지만 성격이 다르다.

| 구분 | 파일 A: XML 샘플 | 파일 B: 출전표 API 문서 |
|---|---:|---:|
| 성격 | 실제 응답 데이터 샘플 | API 명세 문서 |
| 주요 용도 | 경주 결과/기록성 데이터로 보임 | 출전 예정 경주마 정보 |
| `<item>` 기준 컬럼 수 | 90개 | 48개 |
| 데이터 건수 | 10건 | 예제 1건 |
| 공통 컬럼 | 29개 | 29개 |
| 파일 A에만 있는 컬럼 | 61개 | - |
| 파일 B에만 있는 컬럼 | - | 19개 |

---

## 3. 공통 컬럼 29개

두 파일 모두에 있는 컬럼이다.

```txt
meet
rcDate
rcDay
rcNo
chulNo
hrName
hrNo
sex
age
wgBudam
rating
jkName
jkNo
trName
trNo
owName
owNo
ilsu
rcDist
rank
prizeCond
ageCond
budam
rcName
chaksun1
chaksun2
chaksun3
chaksun4
chaksun5
```

### 공통 컬럼의 의미

공통 컬럼들은 대체로 다음 정보를 담고 있다.

| 분류 | 관련 컬럼 |
|---|---|
| 경주 식별 정보 | `meet`, `rcDate`, `rcDay`, `rcNo`, `rcDist`, `rcName` |
| 출전마 정보 | `chulNo`, `hrName`, `hrNo`, `sex`, `age` |
| 기수 정보 | `jkName`, `jkNo` |
| 조교사 정보 | `trName`, `trNo` |
| 마주 정보 | `owName`, `owNo` |
| 경주 조건 | `rank`, `prizeCond`, `ageCond`, `budam`, `rating` |
| 상금 정보 | `chaksun1`, `chaksun2`, `chaksun3`, `chaksun4`, `chaksun5` |

---

## 4. 파일 A에만 있는 컬럼 61개

파일 A에는 실제 경주 결과 또는 기록성 데이터로 보이는 컬럼이 많다.

```txt
birthday
buG1fAccTime
buG1fOrd
buG2fAccTime
buG2fOrd
buG3fAccTime
buG3fOrd
buG4fAccTime
buG4fOrd
buG6fAccTime
buG6fOrd
buG8fAccTime
buG8fOrd
buS1fAccTime
buS1fOrd
buS1fTime
bu_10_8fTime
bu_1fGTime
bu_2fGTime
bu_3fGTime
bu_4_2fTime
bu_6_4fTime
bu_8_6fTime
buga1
buga2
buga3
diffUnit
hrTool
jeG1fTime
jeG3fTime
jeS1fTime
je_1cTime
je_2cTime
je_3cTime
je_4cTime
name
ord
ordBigo
plcOdds
rankRise
rcTime
seG1fAccTime
seG3fAccTime
seS1fAccTime
se_1cAccTime
se_2cAccTime
se_3cAccTime
se_4cAccTime
sjG1fOrd
sjG3fOrd
sjS1fOrd
sj_1cOrd
sj_2cOrd
sj_3cOrd
sj_4cOrd
track
weather
wgBudamBigo
wgHr
wgJk
winOdds
```

### 파일 A 전용 컬럼의 성격

| 분류 | 관련 컬럼 |
|---|---|
| 실제 순위 | `ord`, `ordBigo`, `diffUnit` |
| 배당률 | `winOdds`, `plcOdds` |
| 경주 기록 | `rcTime` |
| 구간 기록 | `seG1fAccTime`, `seG3fAccTime`, `seS1fAccTime`, `se_3cAccTime`, `se_4cAccTime` 등 |
| 통과 순위 | `sjG1fOrd`, `sjG3fOrd`, `sjS1fOrd`, `sj_3cOrd`, `sj_4cOrd` 등 |
| 주로/날씨 | `track`, `weather` |
| 부담중량/마체중 | `wgBudamBigo`, `wgHr`, `wgJk` |
| 장구 정보 | `hrTool` |
| 부가 정보 | `buga1`, `buga2`, `buga3`, `rankRise` |

파일 A는 `race_result_detail` 또는 `race_record_detail` 성격의 테이블로 분리하는 것이 좋다.

---

## 5. 파일 B에만 있는 컬럼 19개

파일 B는 출전표 API 명세 문서이기 때문에 출전 전 참고 정보와 이력성 컬럼이 많다.

```txt
hrNameEn
prd
jkNameEn
trNameEn
owNameEn
dusu
sexCond
stTime
chaksunT
chaksunY
chaksun_6m
ord1CntT
ord2CntT
ord3CntT
rcCntT
ord1CntY
ord2CntY
ord3CntY
rcCntY
```

### 파일 B 전용 컬럼의 성격

| 컬럼 | 의미 |
|---|---|
| `hrNameEn` | 영문 마명 |
| `jkNameEn` | 영문 기수명 |
| `trNameEn` | 영문 조교사명 |
| `owNameEn` | 영문 마주명 |
| `prd` | 산지 |
| `dusu` | 출전 두수 |
| `sexCond` | 성별 조건 |
| `stTime` | 출발 시각 |
| `chaksunT` | 통산 수득상금 |
| `chaksunY` | 최근 1년 수득상금 |
| `chaksun_6m` | 최근 6개월 수득상금 |
| `ord1CntT` | 통산 1위 횟수 |
| `ord2CntT` | 통산 2위 횟수 |
| `ord3CntT` | 통산 3위 횟수 |
| `rcCntT` | 통산 출주 횟수 |
| `ord1CntY` | 최근 1년 1위 횟수 |
| `ord2CntY` | 최근 1년 2위 횟수 |
| `ord3CntY` | 최근 1년 3위 횟수 |
| `rcCntY` | 최근 1년 출주 횟수 |

파일 B는 `race_entry_sheet` 성격의 테이블로 분리하는 것이 좋다.

---

## 6. 결측값 비율

결측값은 두 가지 기준으로 나누어 보는 것이 좋다.

### 6.1 진짜 결측 기준

태그가 없거나 값이 비어 있는 경우만 결측으로 본다.

| 파일 | 데이터 기준 | 전체 셀 수 | 결측 수 | 결측률 |
|---|---:|---:|---:|---:|
| 파일 A XML 샘플 | 10건 × 90컬럼 | 900 | 0 | 0.00% |
| 파일 B 문서 예제 | 1건 × 48컬럼 | 48 | 0 | 0.00% |

빈 태그 또는 누락 태그 기준으로는 두 파일 모두 결측이 없다.

---

### 6.2 `-` 값을 결측으로 처리하는 기준

공공데이터에서 `-`는 값 없음, 해당 없음, 비고 없음처럼 쓰이는 경우가 많다.  
따라서 분석 또는 모델 학습에서는 `-`를 결측으로 처리하는 편이 안전하다.

| 파일 | 전체 셀 수 | `-` 값 개수 | `-` 포함 결측률 |
|---|---:|---:|---:|
| 파일 A XML 샘플 | 900 | 22 | 약 2.44% |
| 파일 B 문서 예제 | 48 | 1 | 약 2.08% |

---

### 6.3 파일 A에서 `-`가 나온 컬럼

| 컬럼 | `-` 개수 | 비율 | 해석 |
|---|---:|---:|---|
| `diffUnit` | 1/10 | 10% | 착차 없음 또는 1위라서 해당 없음 가능성 |
| `hrTool` | 1/10 | 10% | 장구 정보 없음 |
| `ordBigo` | 10/10 | 100% | 순위 비고 없음 |
| `wgBudamBigo` | 10/10 | 100% | 부담중량 비고 없음 |

`ordBigo`, `wgBudamBigo`는 현재 샘플 기준으로 전부 `-`이므로 분석용 피처로서 가치는 낮다.

---

### 6.4 파일 B에서 `-`가 나온 컬럼

| 컬럼 | `-` 개수 | 비율 | 해석 |
|---|---:|---:|---|
| `rating` | 1/1 | 100% | 레이팅 없음 또는 미부여 |

단, 파일 B는 문서 안의 예제 1건 기준이므로 실제 결측률 판단용으로는 표본이 너무 작다.  
정확한 결측률은 실제 API 수집 후 다시 계산해야 한다.

---

## 7. Rate Limit 정리

파일 B 명세 문서 기준으로 확인되는 API 제한 정보는 다음과 같다.

| 항목 | 값 |
|---|---:|
| 서비스 URL | `http://apis.data.go.kr/B551015/API26_2` |
| 상세 기능 URL | `http://apis.data.go.kr/B551015/API26_2/entrySheet_2` |
| 평균 응답 시간 | 500ms |
| 초당 최대 트랜잭션 | 30 TPS |
| 최대 메시지 사이즈 | 4000 byte |
| 인증 방식 | ServiceKey |
| 데이터 형식 | XML |
| 데이터 갱신주기 | 수시 |
| 제한 초과 에러 | `LIMITED_NUMBER_OF_SERVICE_REQUESTS_EXCEEDS_ERROR` |
| 제한 초과 에러 코드 | 22 |

---

## 8. 수집 시 Rate Limit 운영 추천

문서상 초당 최대 트랜잭션은 30 TPS이지만, 실제 수집에서는 여유를 두는 것이 좋다.

### 추천 설정

| 항목 | 추천값 |
|---|---:|
| 초기 요청 속도 | 초당 5~10회 |
| 안정화 후 요청 속도 | 초당 10~15회 |
| 최대 권장 요청 속도 | 초당 20회 이하 |
| 재시도 간격 | 1초 → 2초 → 4초 |
| 제한 초과 시 처리 | 즉시 중단 후 일정 시간 대기 |

30 TPS를 꽉 채워서 호출하면 공공데이터 API 특성상 제한 초과, 일시 장애, 응답 지연이 발생할 수 있다.  
따라서 수집기는 반드시 sleep, retry, backoff 처리를 넣는 것이 안전하다.

---

## 9. DB 설계 관점 추천

두 파일은 하나의 테이블에 억지로 넣기보다 성격별로 분리하는 것이 좋다.

---

### 9.1 출전표 테이블

```txt
race_entry_sheet
```

출전 전 정보 중심 테이블이다.  
파일 B의 48개 컬럼을 기준으로 설계한다.

주요 정보:

- 경주 정보
- 출전마 정보
- 기수/조교사/마주 정보
- 출전 조건
- 최근 성적
- 최근 수득상금
- 출발 시각

---

### 9.2 경주 결과 상세 테이블

```txt
race_result_detail
```

경주 후 결과 및 기록 중심 테이블이다.  
파일 A의 90개 컬럼을 기준으로 설계한다.

주요 정보:

- 실제 순위
- 착차
- 배당률
- 경주 기록
- 구간 기록
- 통과 순위
- 주로 상태
- 날씨
- 마체중
- 부담중량 변경 정보

---

## 10. 공통 키 후보

두 데이터를 연결하기 위한 공통 키 후보는 다음 조합이 적절하다.

```txt
meet
rcDate
rcNo
chulNo
hrNo
```

### 추천 이유

| 컬럼 | 이유 |
|---|---|
| `meet` | 경마장 구분 |
| `rcDate` | 경주일자 |
| `rcNo` | 경주번호 |
| `chulNo` | 출주번호 |
| `hrNo` | 경주마 고유번호 |

특히 `hrNo`는 말 고유번호이므로 반드시 보존하는 것이 좋다.

---

## 11. 추천 Unique Key

DB에서는 아래 조합으로 중복 방지 키를 잡는 것을 추천한다.

```sql
UNIQUE KEY uq_race_horse (
    meet,
    rc_date,
    rc_no,
    chul_no,
    hr_no
)
```

---

## 12. 컬럼명 변환 추천

API 응답은 camelCase가 섞여 있지만 DB에서는 snake_case로 통일하는 것이 좋다.

| API 컬럼명 | DB 컬럼명 |
|---|---|
| `rcDate` | `rc_date` |
| `rcNo` | `rc_no` |
| `chulNo` | `chul_no` |
| `hrName` | `hr_name` |
| `hrNo` | `hr_no` |
| `jkName` | `jk_name` |
| `jkNo` | `jk_no` |
| `trName` | `tr_name` |
| `trNo` | `tr_no` |
| `owName` | `ow_name` |
| `owNo` | `ow_no` |
| `wgBudam` | `wg_budam` |
| `winOdds` | `win_odds` |
| `plcOdds` | `plc_odds` |
| `rcTime` | `rc_time` |

---

## 13. 최종 추천 구조

```txt
race_entry_sheet
    └── 출전 전 정보 저장

race_result_detail
    └── 경주 결과 및 기록 정보 저장
```

두 테이블은 아래 키로 연결한다.

```txt
meet + rc_date + rc_no + chul_no + hr_no
```

---

## 14. 정리

파일 B는 출전 전 데이터이고, 파일 A는 결과/기록 데이터로 보는 것이 자연스럽다.

따라서 최종 구조는 다음과 같다.

| 데이터 | 추천 테이블 | 역할 |
|---|---|---|
| 파일 B API 명세 | `race_entry_sheet` | 출전표, 출전마 기본 이력 |
| 파일 A XML 샘플 | `race_result_detail` | 경주 결과, 기록, 배당률, 날씨, 주로 상태 |

이렇게 분리하면 이후에 다음 작업이 쉬워진다.

- API별 수집기 분리
- 테이블별 책임 분리
- 결측값 관리
- 모델 학습용 피처 선정
- 경주 전 예측 데이터와 경주 후 결과 데이터 비교
