import asyncio
import os
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from ..core.database import get_db
from ..core.models import Movie
from ..core.config import get_settings
from ..core.security import admin_user
from typing import Dict

settings = get_settings()
router = APIRouter(dependencies=[Depends(admin_user)])

def _allowed_upload_roots() -> list[str]:
    roots = []
    for raw in (settings.UPLOAD_ROOTS or "").split(","):
        raw = raw.strip()
        if not raw:
            continue
        roots.append(os.path.normcase(os.path.realpath(os.path.abspath(raw))))
    return roots

def _validate_scan_path(path: str) -> str:
    if not path or not str(path).strip():
        raise HTTPException(status_code=400, detail="Path is required")
    candidate = os.path.normcase(os.path.realpath(os.path.abspath(str(path).strip())))
    roots = _allowed_upload_roots()
    if not roots:
        raise HTTPException(status_code=503, detail="UPLOAD_ROOTS is not configured")

    allowed = any(
        candidate == root or candidate.startswith(root + os.sep)
        for root in roots
    )
    if not allowed:
        raise HTTPException(status_code=403, detail="Path is outside allowed upload roots")
    if not os.path.exists(candidate):
        raise HTTPException(status_code=404, detail="Path not found")
    return candidate

@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    from ..services.upload_service import UploadService
    movie_count = await db.execute(select(func.count(Movie.id)))
    return {
        "total_movies": movie_count.scalar(),
        "server_status": "Online",
        "upload_speed_limit": settings.UPLOAD_SPEED_LIMIT_MB,
        "upload_status": UploadService.get_instance().get_status()
    }

@router.post("/upload/scan")
async def trigger_scan(path: str = Body(..., embed=True)):
    from ..services.upload_service import UploadService
    safe_path = _validate_scan_path(path)
    upload_service = UploadService.get_instance()
    if upload_service.is_uploading:
        raise HTTPException(status_code=400, detail="An upload process is already running")
    asyncio.create_task(upload_service.scan_and_upload(safe_path))
    return {"status": "started", "message": "Scanning started"}

@router.post("/cleanup/duplicates")
async def cleanup_duplicates():
    from ..services.movie_cleaner_service import MovieCleanerService
    cleaner = MovieCleanerService()
    summary = await cleaner.clean_duplicates()
    return {"status": "ok", "data": summary}

@router.get("/movies")
async def list_movies_admin(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Movie).order_by(Movie.id.desc()))
    return result.scalars().all()

@router.delete("/movies/{movie_id}")
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    from ..core.models import movie_categories, WatchHistory
    try:
        await db.execute(movie_categories.delete().where(movie_categories.c.movie_id == movie_id))
        await db.execute(delete(WatchHistory).where(WatchHistory.movie_id == movie_id))
        await db.execute(delete(Movie).where(Movie.id == movie_id))
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Delete failed")
    return {"status": "ok", "message": "Movie removed from database"}


@router.post("/config/upload-limit")
async def update_upload_limit(data: Dict[str, float] = Body(...)):
    limit = data.get("limit")
    if limit is None or limit < 0 or limit > 100:
        raise HTTPException(status_code=400, detail="Limit must be between 0 and 100 MB/s")
    settings.UPLOAD_SPEED_LIMIT_MB = float(limit)
    return {"status": "ok", "message": "Upload speed limit updated"}
