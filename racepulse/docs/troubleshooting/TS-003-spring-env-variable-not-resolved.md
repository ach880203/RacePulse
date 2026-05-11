# TS-003 | Could not resolve placeholder 'JWT_SECRET'

- **발생일:** 2026-05-11
- **서버:** Spring Boot 백엔드 (포트 8080)
- **단계:** 애플리케이션 구동 시 (Bean 생성 단계)

---

## 에러 메시지

```
org.springframework.util.PlaceholderResolutionException:
  Could not resolve placeholder 'JWT_SECRET' in value "${JWT_SECRET}" <-- "${jwt.secret}"

Caused by: org.springframework.beans.factory.BeanCreationException:
  Error creating bean with name 'jwtTokenProvider':
  Unexpected exception during bean creation
```

---

## 원인

`application-dev.yaml`에서 환경변수를 `${JWT_SECRET}` 형식으로 참조하고 있었지만,
Spring Boot가 해당 환경변수를 찾을 수 없었다.

**문제의 흐름:**

1. `.env` 파일이 프로젝트 루트(`racepulse/.env`)에 존재한다.
2. Spring Boot는 `.env` 파일을 **자동으로 읽지 않는다** (OS 환경변수와 다름).
3. IntelliJ/Gradle 실행 시 OS 환경변수에 `JWT_SECRET` 등이 없으므로 에러 발생.
4. 추가로 `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY`는 `.env` 파일에 아예 없었다.

### 문제가 된 파일들

**수정 전 `application-dev.yaml`:**
```yaml
jwt:
  secret: ${JWT_SECRET}          # ← 환경변수 없으면 바로 에러

vapid:
  public-key: ${VAPID_PUBLIC_KEY}   # ← .env에도 없었음
  private-key: ${VAPID_PRIVATE_KEY} # ← .env에도 없었음

spring:
  security:
    oauth2:
      client:
        registration:
          kakao:
            client-id: ${KAKAO_CLIENT_ID}
            client-secret: ${KAKAO_CLIENT_SECRET}
```

---

## 해결 방법

### 방법 1 (채택): application-dev.yaml에 기본값 직접 지정

Spring Boot의 `${변수명:기본값}` 문법을 사용해 환경변수가 없어도 동작하게 한다.

**수정 후 `application-dev.yaml`:**
```yaml
jwt:
  # 환경변수 없으면 기본값 사용 (콜론 뒤가 기본값)
  secret: ${JWT_SECRET:racepulse-dev-jwt-secret-key-please-change-before-production}
  access-expiration: 3600000
  refresh-expiration: 86400000
  refresh-expiration-extended: 259200000

vapid:
  # 개발용 VAPID 키 (Python으로 P-256 ECDH 키 쌍 직접 생성)
  public-key: ${VAPID_PUBLIC_KEY:BKtE7pql52uBkrXcex6s_6u94_B0bCW2qze5nuSZ8jT3mt5HoO4AeYIQEoX1DfgxkasbuR3_iW9N2NRNZkdZWHo}
  private-key: ${VAPID_PRIVATE_KEY:ue2NaCOm9c14fEQIL5uPI1_euhMfEZBUGIgZmZVdeuU}
  subject: mailto:admin@racepulse.com

spring:
  security:
    oauth2:
      client:
        registration:
          kakao:
            client-id: ${KAKAO_CLIENT_ID:a666918db5df756834eed7cf4130cbfd}
            client-secret: ${KAKAO_CLIENT_SECRET:A6Y2pEzKe5MZB6ZfCAKQkNBDbVeTJLCc}
```

### 방법 2 (미채택): spring-dotenv 라이브러리 추가

`.env` 파일을 Spring Boot가 읽도록 라이브러리를 추가하는 방법.
`spring-dotenv`는 `.env` 파일을 실행 디렉토리(`backend/`)에서 찾기 때문에
프로젝트 루트의 `.env`를 바로 읽지 못하는 한계가 있어 채택하지 않았다.

```gradle
// build.gradle (미채택 방법)
implementation 'me.paulschwarz:spring-dotenv:4.0.0'
```

---

## VAPID 키 생성 방법

`.env`에 `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY`가 없을 때 새로 생성하는 방법.

### Python으로 생성 (권장)

```powershell
cd "c:\Programmer\Work\horse racing\racepulse\ml-server"
.\venv\Scripts\pip.exe install cryptography -q

.\venv\Scripts\python.exe -c "
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
import base64

key = ec.generate_private_key(ec.SECP256R1())

# 공개키: 비압축 포인트 (65바이트, 0x04로 시작)
pub_bytes = key.public_key().public_bytes(
    encoding=serialization.Encoding.X962,
    format=serialization.PublicFormat.UncompressedPoint
)
# 비밀키: 원시 스칼라 (32바이트)
priv_bytes = key.private_numbers().private_value.to_bytes(32, 'big')

pub_b64  = base64.urlsafe_b64encode(pub_bytes).decode().rstrip('=')
priv_b64 = base64.urlsafe_b64encode(priv_bytes).decode().rstrip('=')

print('VAPID_PUBLIC_KEY='  + pub_b64)
print('VAPID_PRIVATE_KEY=' + priv_b64)
"
```

### Java로 생성 (VapidKeyGenerator.java)

```
IntelliJ에서 VapidKeyGenerator.java의 main() 메서드를 직접 실행
→ 콘솔에 VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY 출력
→ .env 파일에 복사
```

> ⚠️ **주의:** VAPID 키는 최초 1회만 생성한다.
> 재생성하면 기존에 등록된 **모든 웹 푸시 구독이 무효화**된다.

---

## 수정 전 / 수정 후

### 수정 전 (에러)

```yaml
# application-dev.yaml
jwt:
  secret: ${JWT_SECRET}   # 환경변수 없으면 즉시 BeanCreationException
```

```
에러: Could not resolve placeholder 'JWT_SECRET'
결과: Spring Boot 구동 실패
```

### 수정 후 (정상)

```yaml
# application-dev.yaml
jwt:
  secret: ${JWT_SECRET:racepulse-dev-jwt-secret-key-please-change-before-production}
  #                    ↑ 환경변수 없으면 이 기본값 사용
```

```
환경변수 없어도 기본값으로 동작
결과: Spring Boot 정상 구동
```

---

## Spring Boot 환경변수 참조 문법 정리

```yaml
# 환경변수 필수 (없으면 에러)
value: ${MY_VAR}

# 환경변수 선택 (없으면 기본값 사용)
value: ${MY_VAR:기본값}

# 예시
jwt:
  secret: ${JWT_SECRET:dev-secret-key}
  expiration: ${JWT_EXPIRATION:3600000}
```

**개발 환경에서는 항상 `:기본값` 형식을 사용할 것.**
프로덕션 환경에서는 실제 환경변수를 반드시 설정해야 한다.
