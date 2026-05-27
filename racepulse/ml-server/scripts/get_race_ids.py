"""오늘·내일 race_id 조회 스크립트"""
import asyncio
import sys
sys.path.insert(0, '.')

async def main():
    from app.core.database import AsyncSessionLocal
    from sqlalchemy import text

    async with AsyncSessionLocal() as db:
        result = await db.execute(text(
            "SELECT id, rc_date, meet_code, race_no FROM races "
            "WHERE rc_date IN ('2026-05-23','2026-05-24') "
            "ORDER BY rc_date, meet_code, race_no"
        ))
        rows = result.fetchall()
        print(f"총 {len(rows)}개 경주")
        for r in rows:
            print(f"  race_id={r[0]} | {r[1]} | {r[2]} | {r[3]}경주")

asyncio.run(main())
