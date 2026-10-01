from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.models import Movie, WatchHistory
from ..core.security import authorized_user

router = APIRouter()
COMPLETED_THRESHOLD = 0.90


class RecordWatchRequest(BaseModel):
    movie_id: int = Field(gt=0)
    progress_seconds: float = Field(ge=0, le=604800)
    duration_seconds: float = Field(ge=0, le=604800)


class HistoryItemSchema(BaseModel):
    movie_id: int
    title: str
    poster_url: Optional[str]
    progress_seconds: float
    duration_seconds: float
    watch_count: int
    last_watched_at: str
    progress_percent: float
    global_views: int


def _calc_percent(progress: float, duration: float) -> float:
    if not duration or duration <= 0:
        return 0.0
    return round(min(max(progress, 0.0) / duration, 1.0) * 100, 1)


@router.post("/record")
async def record_watch(
    body: RecordWatchRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(authorized_user),
):
    movie_exists = await db.scalar(select(Movie.id).where(Movie.id == body.movie_id))
    if not movie_exists:
        raise HTTPException(status_code=404, detail="Movie not found")

    progress = body.progress_seconds
    if body.duration_seconds > 0:
        progress = min(progress, body.duration_seconds)

    telegram_id = str(user["id"])
    now_iso = datetime.now(timezone.utc).isoformat()
    stmt = sqlite_insert(WatchHistory).values(
        user_telegram_id=telegram_id,
        movie_id=body.movie_id,
        progress_seconds=progress,
        duration_seconds=body.duration_seconds,
        watch_count=1,
        last_watched_at=now_iso,
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=["user_telegram_id", "movie_id"],
        set_={
            "progress_seconds": progress,
            "duration_seconds": body.duration_seconds,
            "watch_count": WatchHistory.watch_count + 1,
            "last_watched_at": now_iso,
        },
    )
    await db.execute(stmt)
    await db.commit()
    return {"ok": True}


@router.get("/list", response_model=list[HistoryItemSchema])
async def list_history(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(authorized_user),
):
    telegram_id = str(user["id"])
    result = await db.execute(
        select(WatchHistory)
        .where(WatchHistory.user_telegram_id == telegram_id)
        .order_by(WatchHistory.last_watched_at.desc())
        .limit(limit)
    )
    rows = result.scalars().all()
    return [
        HistoryItemSchema(
            movie_id=row.movie_id,
            title=row.movie.title,
            poster_url=row.movie.poster_url,
            progress_seconds=row.progress_seconds,
            duration_seconds=row.duration_seconds,
            watch_count=row.watch_count,
            last_watched_at=row.last_watched_at,
            progress_percent=_calc_percent(row.progress_seconds, row.duration_seconds),
            global_views=row.movie.views,
        )
        for row in rows
        if row.movie
    ]


@router.get("/recommendations", response_model=list[dict])
async def get_recommendations(
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(authorized_user),
):
    telegram_id = str(user["id"])
    hist_result = await db.execute(
        select(WatchHistory).where(WatchHistory.user_telegram_id == telegram_id)
    )
    histories = {row.movie_id: row for row in hist_result.scalars().all()}

    completed_ids = {
        mid
        for mid, row in histories.items()
        if _calc_percent(row.progress_seconds, row.duration_seconds) >= COMPLETED_THRESHOLD * 100
    }
    unfinished = [row for mid, row in histories.items() if mid not in completed_ids]
    unfinished.sort(key=lambda row: row.last_watched_at, reverse=True)

    movie_result = await db.execute(select(Movie).order_by(Movie.id.desc()))
    all_movies = movie_result.scalars().all()
    watched_ids = set(histories)
    unwatched = [movie for movie in all_movies if movie.id not in watched_ids]

    recommendations = []
    for row in unfinished:
        if row.movie:
            recommendations.append({
                "movie_id": row.movie_id,
                "title": row.movie.title,
                "poster_url": row.movie.poster_url,
                "progress_seconds": row.progress_seconds,
                "duration_seconds": row.duration_seconds,
                "progress_percent": _calc_percent(row.progress_seconds, row.duration_seconds),
                "reason": "unfinished",
                "global_views": row.movie.views,
            })
            if len(recommendations) >= limit:
                return recommendations

    for movie in unwatched:
        recommendations.append({
            "movie_id": movie.id,
            "title": movie.title,
            "poster_url": movie.poster_url,
            "progress_seconds": 0,
            "duration_seconds": 0,
            "progress_percent": 0,
            "reason": "unwatched",
            "global_views": movie.views,
        })
        if len(recommendations) >= limit:
            break
    return recommendations
