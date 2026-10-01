from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.models import Category, Movie
from ..core.security import authorized_user

router = APIRouter()


class MovieSchema(BaseModel):
    id: int
    title: str
    description: Optional[str]
    poster_url: Optional[str]
    backdrop_url: Optional[str]
    release_year: Optional[int]
    rating: Optional[float]
    views: int
    size_bytes: Optional[int] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


@router.get("/movies", response_model=List[MovieSchema])
async def list_movies(
    skip: int = Query(0, ge=0, le=1_000_000),
    limit: int = Query(20, ge=1, le=10000),
    search: Optional[str] = Query(None, max_length=200),
    category_id: Optional[int] = Query(None, gt=0),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(authorized_user),
):
    query = select(Movie)
    if search:
        query = query.where(Movie.title.ilike(f"%{search.strip()}%"))
    if category_id:
        query = query.join(Movie.categories).where(Category.id == category_id)
    query = query.order_by(Movie.id.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/movies/{movie_id}", response_model=MovieSchema)
async def get_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(authorized_user),
):
    movie = await db.scalar(select(Movie).where(Movie.id == movie_id))
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie


@router.post("/movies/{movie_id}/view")
async def increment_view(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(authorized_user),
):
    movie = await db.scalar(select(Movie).where(Movie.id == movie_id))
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    movie.views = (movie.views or 0) + 1
    await db.commit()
    return {"ok": True, "views": movie.views}
