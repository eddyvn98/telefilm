from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from typing import List, Optional
from pydantic import BaseModel
from ..core.database import get_db
from ..core.models import Movie, Category
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
    skip: int = 0, 
    limit: int = 20, 
    search: Optional[str] = None,
    category_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(authorized_user)
):
    query = select(Movie)
    
    if search:
        query = query.where(Movie.title.ilike(f"%{search}%"))
    
    if category_id:
         query = query.join(Movie.categories).where(Category.id == category_id)
         
    query = query.order_by(Movie.id.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    movies = result.scalars().all()
    return movies

@router.get("/movies/{movie_id}", response_model=MovieSchema)
async def get_movie(
    movie_id: int, 
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(authorized_user)
):
    result = await db.execute(select(Movie).where(Movie.id == movie_id))
    movie = result.scalar_one_or_none()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie

@router.post("/movies/{movie_id}/view")
async def increment_view(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(authorized_user)
):
    result = await db.execute(select(Movie).where(Movie.id == movie_id))
    movie = result.scalar_one_or_none()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    movie.views += 1
    await db.commit()
    return {"ok": True, "views": movie.views}
