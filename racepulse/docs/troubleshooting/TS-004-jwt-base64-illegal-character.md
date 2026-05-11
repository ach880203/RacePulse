# TS-004 | DecodingException: Illegal base64 character '-'

- **발생일:** 2026-05-11
- **서버:** Spring Boot 백엔드 (포트 8080)
- **단계:** 애플리케이션 구동 시 (JwtTokenProvider Bean 생성)

---

## 에러 메시지

```
Caused by: io.jsonwebtoken.io.DecodingException: Illegal base64 character: '-'
    at io.jsonwebtoken.io.Base64.ctoi(Base64.java:221)
    at io.jsonwebtoken.io.Base64.decodeFast(Base64.java:271)
    at com.racepulse.backend.global.security.JwtTokenProvider.<init>(JwtTokenProvider.java:56)
```

---

## 원인

`JwtTokenProvider` 생성자에서 JWT 시크릿 키를 `Decoders.BASE64.decode(secret)`으로 디코딩하는데,
시크릿 값 `racepulse-dev-jwt-secret-key-...`에 하이픈(`-`)이 포함되어 있어 표준 Base64 디코딩 실패.

| Base64 종류 | 허용 문자 | 사용처 |
|-------------|-----------|--------|
| 표준 Base64 | `A-Z a-z 0-9 + / =` | 일반 인코딩 |
| Base64URL   | `A-Z a-z 0-9 - _ =` | URL, JWT 등 |
| 평문 문자열 | 모든 문자 | 사람이 읽는 시크릿 |

시크릿 값은 Base64가 아닌 **평문 문자열**인데 `Decoders.BASE64.decode()`를 호출한 것이 원인.

### 문제가 된 코드

```java
// JwtTokenProvider.java — 수정 전
public JwtTokenProvider(@Value("${jwt.secret}") String secret, ...) {
    // Base64 디코딩 강제 → '-' 문자가 있으면 DecodingException 발생!
    this.secretKey = Keys.hmacShaKeyFor(Decoders.BASE64.decode(secret));
}
```

---

## 해결 방법

`decodeSecret()` 헬퍼를 추가해서 입력값 형식을 자동으로 판단.

```java
// JwtTokenProvider.java — 수정 후
import java.nio.charset.StandardCharsets;
import java.util.Base64;

public JwtTokenProvider(@Value("${jwt.secret}") String secret, ...) {
    // 형식 자동 판단 후 변환
    this.secretKey = Keys.hmacShaKeyFor(decodeSecret(secret));
}

private byte[] decodeSecret(String secret) {
    try {
        // 1순위: 표준 Base64 시도
        return Base64.getDecoder().decode(secret);
    } catch (IllegalArgumentException e1) {
        try {
            // 2순위: Base64URL 시도 (-, _ 허용)
            return Base64.getUrlDecoder().decode(secret);
        } catch (IllegalArgumentException e2) {
            // 3순위: 평문 문자열 → UTF-8 바이트 그대로 사용
            return secret.getBytes(StandardCharsets.UTF_8);
        }
    }
}
```

이 방식으로 `jwt.secret`에 어떤 형식의 값이 와도 정상 동작한다.

---

## 수정 전 / 수정 후

### 수정 전 (에러)

```yaml
# application-dev.yaml
jwt:
  secret: ${JWT_SECRET:racepulse-dev-jwt-secret-key-please-change-before-production}
  # ↑ 하이픈(-) 포함 → Decoders.BASE64.decode() 실패
```

```
DecodingException: Illegal base64 character: '-'
→ Spring Boot 구동 실패
```

### 수정 후 (정상)

```yaml
# application-dev.yaml (변경 없음, 그대로 사용 가능)
jwt:
  secret: ${JWT_SECRET:racepulse-dev-jwt-secret-key-please-change-before-production}
```

```java
// decodeSecret() 내부에서 자동 판단
// → 표준 Base64 실패 → Base64URL 실패 → UTF-8 바이트로 변환 → 정상 동작
```

---

## 프로덕션 환경 권장 시크릿 생성 방법

프로덕션에서는 반드시 충분한 길이의 랜덤 키를 사용해야 한다.
HMAC-SHA256 최소 요구 길이: **256비트(32바이트) 이상**

```powershell
# PowerShell로 안전한 Base64 시크릿 생성 (64바이트 = 512비트)
$bytes = New-Object byte[] 64
[System.Security.Cryptography.RandomNumberGenerator]::Fill($bytes)
[Convert]::ToBase64String($bytes)
# 결과 예: xK9m2P+tQr... → .env의 JWT_SECRET에 저장
```

```bash
# Linux/Mac
openssl rand -base64 64
```
