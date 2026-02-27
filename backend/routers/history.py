from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone

from ..core.database import get_db
from ..core.models import Movie, WatchHistory
from ..core.security import authorized_user

router = APIRouter()

COMPLETED_THRESHOLD = 0.90  # 90% = watched


# ── Schemas ───────────────────────────────────────────────────────────────────

class RecordWatchRequest(BaseModel):
    movie_id: int
    progress_seconds: float
    duration_seconds: float


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

    class Config:
        from_attributes = True


# ── Helpers ───────────────────────────────────────────────────────────────────

def _calc_percent(progress: float, duration: float) -> float:
    if not duration or duration <= 0:
        return 0.0
    return round(min(progress / duration, 1.0) * 100, 1)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/record", status_code=200)
async def record_watch(
    body: RecordWatchRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(authorized_user),
):
    """Upsert watch history for the current user + movie."""
    telegram_id = str(user["id"])
    now_iso = datetime.now(timezone.utc).isoformat()

    result = await db.execute(
        select(WatchHistory).where(
            and_(
                WatchHistory.user_telegram_id == telegram_id,
                WatchHistory.movie_id == body.movie_id,
            )
        )
    )
    entry = result.scalar_one_or_none()

    if entry:
        entry.progress_seconds = body.progress_seconds
        entry.duration_seconds = body.duration_seconds
        entry.watch_count += 1
        entry.last_watched_at = now_iso
    else:
        entry = WatchHistory(
            user_telegram_id=telegram_id,
            movie_id=body.movie_id,
            progress_seconds=body.progress_seconds,
            duration_seconds=body.duration_seconds,
            watch_count=1,
            last_watched_at=now_iso,
        )
        db.add(entry)

    await db.commit()
    return {"ok": True}


@router.get("/list", response_model=list[HistoryItemSchema])
async def list_history(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(authorized_user),
):
    """Return recently watched movies, newest first."""
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
            global_views=row.movie.views
        )
        for row in rows if row.movie
    ]


@router.get("/recommendations", response_model=list[dict])
async def get_recommendations(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(authorized_user),
):
    """Suggest: unwatched + unfinished movies (progress < 90%)."""
    telegram_id = str(user["id"])

    # Get all watched histories for this user
    hist_result = await db.execute(
        select(WatchHistory).where(WatchHistory.user_telegram_id == telegram_id)
    )
    histories = {row.movie_id: row for row in hist_result.scalars().all()}

    # Collect IDs that are "completed" (>= 90%)
    completed_ids = {
        mid for mid, row in histories.items()
        if _calc_percent(row.progress_seconds, row.duration_seconds) >= COMPLETED_THRESHOLD * 100
    }

    # Priority 1: Unfinished (watched but < 90%) – sorted by most recently watched
    unfinished = [
        row for mid, row in histories.items()
        if mid not in completed_ids
    ]
    unfinished.sort(key=lambda r: r.last_watched_at, reverse=True)

    # Get all movies
    all_movies_result = await db.execute(select(Movie))
    all_movies = all_movies_result.scalars().all()

    # Priority 2: Never watched
    watched_ids = set(histories.keys())
    unwatched = [m for m in all_movies if m.id not in watched_ids]

    recommendations = []

    # Add unfinished first
    for row in unfinished:
        if not row.movie:
            continue
        recommendations.append({
            "movie_id": row.movie_id,
            "title": row.movie.title,
            "poster_url": row.movie.poster_url,
            "progress_seconds": row.progress_seconds,
            "duration_seconds": row.duration_seconds,
            "progress_percent": _calc_percent(row.progress_seconds, row.duration_seconds),
            "reason": "unfinished",
            "global_views": row.movie.views
        })

    # Fill with unwatched
    for movie in unwatched:
        if len(recommendations) >= limit:
            break
        recommendations.append({
            "movie_id": movie.id,
            "title": movie.title,
            "poster_url": movie.poster_url,
            "progress_seconds": 0,
            "duration_seconds": 0,
            "progress_percent": 0,
            "reason": "unwatched",
            "global_views": movie.views
        })

    return recommendations[:limit]
