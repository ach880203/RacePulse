# =============================================================================
# health.py — 헬스체크 API
# =============================================================================

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import get_db

router = APIRouter()


# -----------------------------------------------------------------------------
# 기본 헬스체크
# DB 연결 없이 서버가 살아있는지만 확인
# -----------------------------------------------------------------------------
@router.get("/health")
async def health():
    return {
        "status": "UP",
        "service": "RacePulse ML Server"
    }


# -----------------------------------------------------------------------------
# DB 연결 헬스체크
# Depends(get_db) = database.py의 get_db 함수에서 DB 세션을 받아옴
# text("SELECT 1") = DB에 가장 간단한 쿼리를 보내서 연결 확인
# SELECT version() = PostgreSQL 버전 정보 조회
# -----------------------------------------------------------------------------
@router.get("/health/db")
async def health_db(db: AsyncSession = Depends(get_db)):
    # DB에 쿼리 실행
    result = await db.execute(text("SELECT version()"))

    # 결과에서 버전 정보 꺼내기
    version = result.scalar()

    return {
        "status": "UP",
        "database": "connected",
        "postgresql_version": version
    }