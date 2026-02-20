import asyncio
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from ..core.database import get_db
from ..core.models import Movie
from ..core.config import get_settings
from typing import Dict

settings = get_settings()
router = APIRouter()

@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    from ..services.upload_service import UploadService
    movie_count = await db.execute(select(func.count(Movie.id)))
    return {
        "total_movies": movie_count.scalar(),
        "server_status": "Online",
        "webapp_url": settings.WEBAPP_URL,
        "upload_speed_limit": settings.UPLOAD_SPEED_LIMIT_MB,
        "upload_status": UploadService.get_instance().get_status()
    }

@router.post("/upload/scan")
async def trigger_scan(path: str = Body(..., embed=True)):
    print(f"DEBUG: Triggering scan for path: {path}", flush=True)
    from ..services.upload_service import UploadService
    upload_service = UploadService.get_instance()
    if upload_service.is_uploading:
        print("DEBUG: Already uploading", flush=True)
        raise HTTPException(status_code=400, detail="An upload process is already running")
    
    # Run in background
    print("DEBUG: Creating background task", flush=True)
    asyncio.create_task(upload_service.scan_and_upload(path))
    return {"status": "started", "message": f"Scanning started for {path}"}

@router.get("/movies")
async def list_movies_admin(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Movie).order_by(Movie.id.desc()))
    return result.scalars().all()

@router.delete("/movies/{movie_id}")
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    from ..core.models import movie_categories
    print(f"DEBUG: Deleting movie {movie_id}", flush=True)
    try:
        # 1. Delete links in the association table first
        await db.execute(movie_categories.delete().where(movie_categories.c.movie_id == movie_id))
        # 2. Delete the movie
        await db.execute(delete(Movie).where(Movie.id == movie_id))
        await db.commit()
    except Exception as e:
        await db.rollback()
        print(f"ERROR: Delete failed: {e}", flush=True)
        raise HTTPException(status_code=500, detail=str(e))
        
    return {"status": "ok", "message": "Movie removed from database"}

@router.post("/config/webapp-url")
async def update_webapp_url(data: Dict[str, str] = Body(...)):
    url = data.get("url")
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")
    
    settings.WEBAPP_URL = url
    print(f"✅ WebApp URL updated to {url}", flush=True)
    return {"status": "ok", "message": f"URL updated to {url}"}

@router.post("/config/upload-limit")
async def update_upload_limit(data: Dict[str, float] = Body(...)):
    limit = data.get("limit")
    if limit is None:
        raise HTTPException(status_code=400, detail="Limit is required")
    
    settings.UPLOAD_SPEED_LIMIT_MB = limit
    print(f"🚀 Upload speed limit updated to {limit} MB/s", flush=True)
    return {"status": "ok", "message": f"Upload speed limit updated to {limit} MB/s"}
