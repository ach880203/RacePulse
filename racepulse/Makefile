# =============================================================================
# RacePulse - Makefile
# =============================================================================
# 사용법: make <명령어>
# 예시:   make up
# =============================================================================

# .env 파일이 없으면 경고 출력
ifeq (,$(wildcard .env))
$(warning [경고] .env 파일이 없습니다. .env.example을 복사해 .env를 만들어 주세요.)
$(warning 실행: cp .env.example .env)
endif

.PHONY: up down logs ps reset help

## 도움말 출력 (기본 명령어)
help:
	@echo ""
	@echo "RacePulse 로컬 개발 환경 명령어"
	@echo "=================================="
	@echo "  make up      - 모든 서비스 백그라운드 실행"
	@echo "  make down    - 모든 서비스 중지 및 컨테이너 제거"
	@echo "  make logs    - 전체 로그 스트리밍 (Ctrl+C로 종료)"
	@echo "  make ps      - 실행 중인 컨테이너 상태 확인"
	@echo "  make reset   - 볼륨 포함 전체 초기화 후 재시작 (데이터 삭제!)"
	@echo ""

## 모든 서비스 백그라운드 실행
up:
	@echo ">>> RacePulse 서비스를 시작합니다..."
	docker-compose up -d
	@echo ">>> 서비스가 시작되었습니다."
	@echo "    PostgreSQL : localhost:5432"
	@echo "    Redis      : localhost:6379"
	@echo "    Backend    : localhost:8080"
	@echo "    ML Server  : localhost:8000"

## 모든 서비스 중지 및 컨테이너 제거 (볼륨은 유지)
down:
	@echo ">>> RacePulse 서비스를 중지합니다..."
	docker-compose down
	@echo ">>> 서비스가 중지되었습니다. (데이터 볼륨은 유지됨)"

## 전체 로그 실시간 스트리밍
logs:
	docker-compose logs -f

## 특정 서비스 로그 (예: make logs-backend)
logs-%:
	docker-compose logs -f $*

## 컨테이너 상태 확인
ps:
	docker-compose ps

## 볼륨 포함 전체 초기화 후 재시작 (데이터 완전 삭제 주의!)
reset:
	@echo ">>> [경고] 모든 데이터(DB, Redis)가 삭제됩니다!"
	@read -p "계속 진행하시겠습니까? (yes/N): " confirm && [ "$$confirm" = "yes" ] || (echo "취소되었습니다." && exit 1)
	@echo ">>> 서비스 중지 및 볼륨 삭제 중..."
	docker-compose down -v
	@echo ">>> 서비스를 다시 시작합니다..."
	docker-compose up -d
	@echo ">>> 초기화가 완료되었습니다."
