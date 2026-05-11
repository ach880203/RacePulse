# -*- coding: utf-8 -*-
# =============================================================================
# commentary.py — AI 해설 생성 및 조회 API 라우터 (FastAPI)
# =============================================================================
# 이 라우터가 제공하는 엔드포인트:
#   GET  /commentary/{race_id}/pre          → 사전 해설 조회
#   GET  /commentary/{race_id}/post         → 결과 해설 조회
#   POST /admin/commentary/generate/pre/{race_id}  → 사전 해설 수동 생성
#   POST /admin/commentary/generate/post/{race_id} → 결과 해설 수동 생성
#   POST /admin/commentary/regenerate        → 특정 경주 해설 강제 재생성
# =============================================================================

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.ml import AICommentary
from app.services.ai_commentary import AICommentaryService

logger = logging.getLogger(__name__)

# 두 개의 라우터를 만듭니다.
# commentary_router = 조회 API (Spring Boot가 이쪽을 프록시합니다)
# admin_commentary_router = 생성/재생성 관리자 API
commentary_router       = APIRouter(prefix="/commentary")
admin_commentary_router = APIRouter(prefix="/admin/commentary")


# =============================================================================
# 조회 API
# =============================================================================

@commentary_router.get("/{race_id}/pre")
async def get_pre_race_commentary(
    race_id: int,
    db: AsyncSession = Depends(get_db),
):
    """특정 경주의 사전 해설을 조회합니다.

    완료 기준 1: GET /commentary/{race_id}/pre → 사전 해설 조회 성공

    캐시 → DB 순서로 조회합니다. 없으면 404를 반환합니다.
    해설이 아직 생성되지 않았다면 POST /admin/commentary/generate/pre/{race_id} 를 먼저 실행하세요.
    """
    svc = AICommentaryService(db)

    # 1. Redis 캐시 먼저 확인
    race = await db.get(__import__('app.models.race', fromlist=['Race']).Race, race_id)
    if race:
        cache_key = AICommentaryService._make_cache_key(
            "pre_race", race.meet_code, str(race.rc_date), race.race_no
        )
        cached = await svc.get_from_cache(cache_key)
        if cached:
            return {
                "success": True,
                "data": {"raceId": race_id, "type": "PRE", "content": cached, "source": "cache"},
                "message": "사전 해설 조회 성공",
            }

    # 2. DB 조회
    stmt = select(AICommentary).where(
        and_(AICommentary.race_id == race_id, AICommentary.type == "PRE")
    )
    record = await db.scalar(stmt)

    if not record:
        raise HTTPException(
            status_code=404,
            detail=f"race_id={race_id}의 사전 해설이 없습니다. POST /admin/commentary/generate/pre/{race_id} 를 먼저 실행해주세요."
        )

    return {
        "success": True,
        "data": {
            "raceId":       record.race_id,
            "type":         record.type,
            "content":      record.content,
            "modelUsed":    record.model_used,
            "generatedAt":  record.generated_at.isoformat(),
            "source":       "db",
        },
        "message": "사전 해설 조회 성공",
    }


@commentary_router.get("/{race_id}/post")
async def get_post_race_commentary(
    race_id: int,
    db: AsyncSession = Depends(get_db),
):
    """특정 경주의 결과 해설을 조회합니다."""
    stmt = select(AICommentary).where(
        and_(AICommentary.race_id == race_id, AICommentary.type == "POST")
    )
    record = await db.scalar(stmt)

    if not record:
        raise HTTPException(
            status_code=404,
            detail=f"race_id={race_id}의 결과 해설이 없습니다."
        )

    return {
        "success": True,
        "data": {
            "raceId":      record.race_id,
            "type":        record.type,
            "content":     record.content,
            "modelUsed":   record.model_used,
            "generatedAt": record.generated_at.isoformat(),
        },
        "message": "결과 해설 조회 성공",
    }


# =============================================================================
# 관리자 API — 해설 생성 (수동 실행 / 스케줄러에서도 호출)
# =============================================================================

@admin_commentary_router.post("/generate/pre/{race_id}")
async def generate_pre_commentary(
    race_id: int,
    db: AsyncSession = Depends(get_db),
):
    """특정 경주의 사전 해설을 지금 바로 GPT로 생성합니다.

    완료 기준: POST /admin/commentary/generate/pre/1 → GPT 해설 생성
    캐시가 있으면 GPT를 새로 호출하지 않고 캐시를 반환합니다.
    """
    svc = AICommentaryService(db)
    try:
        result = await svc.generate_pre_race_commentary(race_id)
        return {
            "success": True,
            "data": {
                "raceId":   race_id,
                "type":     "PRE",
                "source":   result["source"],   # "gpt" 또는 "cache"
                "cacheKey": result["cache_key"],
                "usage":    result.get("usage"),
                # 본문 앞 200자만 미리보기로 반환합니다.
                "preview":  result["content"][:200] + "...",
            },
            "message": f"사전 해설 생성 완료 (출처: {result['source']})",
        }
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.error("[AI 해설] 사전 해설 생성 실패. race_id=%d, 오류=%s", race_id, exc)
        raise HTTPException(status_code=500, detail=f"해설 생성 실패: {exc}")


@admin_commentary_router.post("/generate/post/{race_id}")
async def generate_post_commentary(
    race_id: int,
    db: AsyncSession = Depends(get_db),
):
    """특정 경주의 결과 해설을 지금 바로 GPT로 생성합니다."""
    svc = AICommentaryService(db)
    try:
        result = await svc.generate_post_race_commentary(race_id)
        return {
            "success": True,
            "data": {
                "raceId":   race_id,
                "type":     "POST",
                "source":   result["source"],
                "cacheKey": result["cache_key"],
                "usage":    result.get("usage"),
                "preview":  result["content"][:200] + "...",
            },
            "message": f"결과 해설 생성 완료 (출처: {result['source']})",
        }
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.error("[AI 해설] 결과 해설 생성 실패. race_id=%d, 오류=%s", race_id, exc)
        raise HTTPException(status_code=500, detail=f"해설 생성 실패: {exc}")


@admin_commentary_router.post("/regenerate")
async def regenerate_commentary(
    race_id: int,
    commentary_type: str = "PRE",
    db: AsyncSession = Depends(get_db),
):
    """기존 해설을 무시하고 GPT를 새로 호출하여 해설을 재생성합니다.

    @param race_id         재생성할 경주 ID
    @param commentary_type "PRE" 또는 "POST"
    """
    # 기존 캐시/DB 레코드를 삭제하여 강제 재생성합니다.
    stmt = select(AICommentary).where(
        and_(
            AICommentary.race_id == race_id,
            AICommentary.type == commentary_type.upper(),
        )
    )
    existing = await db.scalar(stmt)
    if existing:
        await db.delete(existing)
        await db.commit()
        logger.info("[AI 해설] 기존 해설 삭제 완료. race_id=%d type=%s", race_id, commentary_type)

    svc = AICommentaryService(db)
    try:
        if commentary_type.upper() == "PRE":
            result = await svc.generate_pre_race_commentary(race_id)
        else:
            result = await svc.generate_post_race_commentary(race_id)

        return {
            "success": True,
            "data": {
                "raceId":  race_id,
                "type":    commentary_type.upper(),
                "preview": result["content"][:200] + "...",
            },
            "message": "해설 재생성 완료",
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
