# -*- coding: utf-8 -*-
#========================================================================
# database.py - 데이터 베이스 연결 설정 파일
#========================================================================
# 이 파일은 PostgreSQL과 연결을 맺고 관리하는 역할을 합니다.
# SQLAlchemy 라이브러리를 사용해서 Python 코드로 DB를 다룰 수 있게 해줍니다.
#
# [핵심개념]
# - 엔진(engine): DB와 실제로 연결하는 통로
# - 세션(session): DB에 명령을 보내는 작업 단위 (SQL 실행, 커밋 등)
# - Base: 우리가 만들 DB테이블 모델들의 부모 클래스
#========================================================================

# AsyncSession/create_async_engine = SQLAlchemy의 비동기 DB 처리 도구입니다.
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
# DeclarativeBase = ORM 모델들의 공통 부모 클래스입니다.
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# settings = .env 에서 읽은 DB 주소, debug 여부 등을 담고 있는 공통 설정 객체입니다.
from app.core.config import settings

# -----------------------------------------------------------------------------
# 데이터베이스 엔진 생성
# create_async_engine = 비동기 방식으로 DB 연결을 만드는 함수
# echo=settings.debug → True면 실행되는 SQL을 콘솔에 출력 (디버깅용)
# pool_pre_ping=True → DB 연결이 끊겼을 때 자동으로 재연결 시도
# -----------------------------------------------------------------------------
engine = create_async_engine(
    settings.db_url,
    echo=settings.debug,
    pool_pre_ping=True,
)


# -----------------------------------------------------------------------------
# 세션 팩토리 생성
# 세션 = DB에 쿼리를 실행하는 작업 공간
# 요청이 올 때마다 새 세션을 만들고, 끝나면 닫는 방식으로 사용
# expire_on_commit=False → 커밋 후에도 객체 데이터를 메모리에 유지
# -----------------------------------------------------------------------------
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# -----------------------------------------------------------------------------
# Base 클래스
# 우리가 만들 모든 DB 테이블 모델은 이 Base를 상속받아야 함
# 예: class Horse(Base): ← horses 테이블과 연결되는 Python 클래스
# -----------------------------------------------------------------------------
class Base(DeclarativeBase):
    pass


# -----------------------------------------------------------------------------
# DB 세션 의존성 함수
# FastAPI의 각 API 함수에서 DB가 필요할 때 이 함수를 통해 세션을 받아 사용
# yield = 세션을 빌려주고, API 처리가 끝나면 자동으로 세션을 닫아줌
# try/finally = 오류가 나도 반드시 세션이 닫히도록 보장
# -----------------------------------------------------------------------------
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session       # 세션을 API 함수에 전달
        finally:
            await session.close()  # 사용 후 반드시 세션 닫기
