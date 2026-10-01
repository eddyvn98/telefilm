import asyncio

from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import get_settings
from ..core.database import get_db
from ..core.models import Movie
from ..core.paths import validate_upload_path
from ..core.security import admin_user
from ..services.movie_cleaner_service import MovieCleanerService
from ..services.upload_service import UploadService

settings = get_settings()
router = APIRouter(dependencies=[Depends(admin_user)])


class UploadLimitRequest(BaseModel):
    limit: float = Field(ge=0, le=100)


@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    movie_count = await db.scalar(select(func.count(Movie.id)))
    return {
        "total_movies": movie_count or 0,
        "server_status": "Online",
        "upload_speed_limit": settings.UPLOAD_SPEED_LIMIT_MB,
        "upload_status": UploadService.get_instance().get_status(),
    }


@router.post("/upload/scan")
async def trigger_scan(path: str = Body(..., embed=True)):
    safe_path = validate_upload_path(path)
    upload_service = UploadService.get_instance()
    if upload_service.is_uploading:
        raise HTTPException(status_code=409, detail="An upload process is already running")
    asyncio.create_task(upload_service.scan_and_upload(safe_path))
    return {"status": "started", "message": "Scanning started"}


@router.post("/cleanup/duplicates")
async def cleanup_duplicates():
    summary = await MovieCleanerService().clean_duplicates()
    return {"status": "ok", "data": summary}


@router.get("/movies")
async def list_movies_admin(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Movie).order_by(Movie.id.desc()))
    return result.scalars().all()


@router.delete("/movies/{movie_id}")
async def delete_movie(movie_id: int):
    try:
        result = await MovieCleanerService().delete_movie(movie_id)
    except Exception:
        raise HTTPException(status_code=500, detail="Delete failed")
    if not result["found"]:
        raise HTTPException(status_code=404, detail="Movie not found")
    return {"status": "ok", "data": result}


@router.post("/config/upload-limit")
async def update_upload_limit(data: UploadLimitRequest):
    settings.UPLOAD_SPEED_LIMIT_MB = float(data.limit)
    return {
        "status": "ok",
        "message": "Upload speed limit updated for the current server process",
        "limit": settings.UPLOAD_SPEED_LIMIT_MB,
    }
