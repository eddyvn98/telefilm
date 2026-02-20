from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Table
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column
from typing import List, Optional

class Base(DeclarativeBase):
    pass

# Link table for Movie-Category
movie_categories = Table(
    "movie_categories",
    Base.metadata,
    Column("movie_id", Integer, ForeignKey("movies.id"), primary_key=True),
    Column("category_id", Integer, ForeignKey("categories.id"), primary_key=True),
)

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    username: Mapped[Optional[str]] = mapped_column(String)
    first_name: Mapped[Optional[str]] = mapped_column(String)
    photo_url: Mapped[Optional[str]] = mapped_column(String)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[str] = mapped_column(String) # ISO Format

class Category(Base):
    __tablename__ = "categories"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    slug: Mapped[str] = mapped_column(String, unique=True)
    
    movies: Mapped[List["Movie"]] = relationship(secondary=movie_categories, back_populates="categories")

class Movie(Base):
    __tablename__ = "movies"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String, index=True)
    original_title: Mapped[Optional[str]] = mapped_column(String)
    file_id: Mapped[str] = mapped_column(String) # Telegram File ID
    description: Mapped[Optional[str]] = mapped_column(String)
    poster_url: Mapped[Optional[str]] = mapped_column(String) # Or file_id of poster
    backdrop_url: Mapped[Optional[str]] = mapped_column(String)
    release_year: Mapped[Optional[int]] = mapped_column(Integer)
    duration_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    rating: Mapped[Optional[float]] = mapped_column(Integer)
    views: Mapped[int] = mapped_column(Integer, default=0)
    size_bytes: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[Optional[str]] = mapped_column(String) # ISO Format
    
    categories: Mapped[List["Category"]] = relationship(secondary=movie_categories, back_populates="movies")
