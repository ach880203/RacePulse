# -*- coding: utf-8 -*-
# =============================================================================
# main.py — FastAPI 앱의 시작점 (진입점)
# =============================================================================
# 이 파일이 FastAPI 서버의 핵심입니다.
# Spring Boot의 BackendApplication.java 와 같은 역할을 합니다.
# 서버를 실행하면 이 파일이 가장 먼저 실행됩니다.
#
# 이 파일에서 하는 일:
# 1. FastAPI 앱 객체 생성
# 2. CORS 설정 (프론트엔드가 이 서버에 요청할 수 있도록 허용)
# 3. API 라우터 등록 (어떤 URL이 어떤 함수로 연결되는지 등록)
# 4. lifespan 이벤트에서 APScheduler 시작/종료
# =============================================================================

# asynccontextmanager = FastAPI 시작/종료 시점에 실행할 공통 코드를 묶는 도구입니다.
from contextlib import asynccontextmanager

# FastAPI = 파이썬 웹 API 서버를 만드는 프레임워크입니다.
from fastapi import FastAPI
# CORSMiddleware = 다른 포트(예: 3000, 8080)에서 오는 요청을 허용하는 미들웨어입니다.
from fastapi.middleware.cors import CORSMiddleware

# collection_router = 수동 수집 테스트와 상태 조회 API 라우터입니다.
from app.api.collection import router as collection_router
# health_router = 서버 생존 여부와 DB 연결 상태를 확인하는 헬스체크 라우터입니다.
from app.api.health import router as health_router
# weather_router = 경마장별 날씨 조회 API 라우터입니다.
from app.api.weather import router as weather_router
# admin_router = 스케줄러 상태 확인 및 수동 실행 관리자 API 라우터입니다.
from app.api.admin import router as admin_router
# ml_router = ML 피처 계산 및 조회 API 라우터입니다.
from app.api.ml import router as ml_router
# commentary_router / admin_commentary_router = AI 해설 생성 및 조회 라우터입니다.
from app.api.commentary import commentary_router, admin_commentary_router
# settings = 앱 이름, 디버그 여부 같은 공통 설정 객체입니다.
from app.core.config import settings
# close_redis_client = 앱 종료 시 Redis 연결을 정리하는 함수입니다.
from app.core.redis_client import close_redis_client
# CollectionScheduler = APScheduler 작업 등록과 시작/종료를 맡는 래퍼 클래스입니다.
from app.scheduler.scheduler import CollectionScheduler


@asynccontextmanager
async def lifespan(_: FastAPI):
    # FastAPI의 lifespan = 서버가 켜질 때/꺼질 때 한 번씩 실행되는 구간입니다.
    # 여기서 스케줄러와 Redis 연결 정리를 묶어두면 시작/종료 순서를 한 곳에서 관리할 수 있습니다.
    scheduler = CollectionScheduler()
    await scheduler.start()

    try:
        yield
    finally:
        await scheduler.shutdown()
        await close_redis_client()

# -----------------------------------------------------------------------------
# FastAPI 앱 객체 생성
# title, description = /docs 페이지(Swagger)에 표시되는 정보
# docs_url = Swagger UI 접속 주소 → http://localhost:8000/docs
# redoc_url = ReDoc 문서 접속 주소 → http://localhost:8000/redoc
# -----------------------------------------------------------------------------

app = FastAPI(
    title=settings.app_name,
    description="RacePulse ML Server - 경마 데이터 수집 및 예측 및 분석",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


@app.middleware("http")
async def add_charset_header(request, call_next):
    # 일부 클라이언트는 JSON 응답에 charset이 없으면 한글을 잘못 해석할 수 있어 명시적으로 붙입니다.
    response = await call_next(request)
    if response.headers.get("content-type", "").startswith("application/json"):
        response.headers["content-type"] = "application/json; charset=utf-8"
    return response

# -----------------------------------------------------------------------------
# CORS 설정 (Cross-Origin Resource Sharing)
# CORS란? 다른 주소에서 이 서버로 요청하는 것을 허용할지 결정하는 보안 설정
# 예: React(localhost:3000) → FastAPI(localhost:8000) 요청 허용
# allow_origins = 요청을 허용할 주소 목록
# allow_methods=["*"] = GET, POST, PUT, DELETE 등 모든 방식 허용
# allow_headers=["*"] = 모든 헤더 허용
# -----------------------------------------------------------------------------

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",   # Vite 개발 서버
        "http://127.0.0.1:5173",
        "http://localhost:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# -----------------------------------------------------------------------------
# API 라우터 등록
# health_router = health.py 에서 만든 /health 경로를 앱에 연결
# tags=["Health"] = Swagger 문서에서 "Health" 그룹으로 묶임
# -----------------------------------------------------------------------------

# 라우터 등록
app.include_router(health_router, tags=["Health"])
app.include_router(collection_router, tags=["Collection"])
# weather_router = /weather/{meet_code}/{date} 날씨 조회 API를 앱에 연결합니다.
app.include_router(weather_router, tags=["Weather"])
# admin_router = /admin/** 스케줄러 상태 및 수동 실행 API를 앱에 연결합니다.
app.include_router(admin_router, tags=["Admin"])
# ml_router = /ml/** ML 피처 계산 및 조회 API를 앱에 연결합니다.
app.include_router(ml_router, tags=["ML"])
# commentary_router = /commentary/** 해설 조회 API (Spring Boot가 이쪽을 프록시합니다)
app.include_router(commentary_router, tags=["Commentary"])
# admin_commentary_router = /admin/commentary/** 해설 생성 관리자 API
app.include_router(admin_commentary_router, tags=["Admin-Commentary"])
