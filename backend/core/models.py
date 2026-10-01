from typing import List, Optional

from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String, Table, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


movie_categories = Table(
    "movie_categories",
    Base.metadata,
    Column("movie_id", Integer, ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True),
    Column("category_id", Integer, ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    username: Mapped[Optional[str]] = mapped_column(String)
    first_name: Mapped[Optional[str]] = mapped_column(String)
    photo_url: Mapped[Optional[str]] = mapped_column(String)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[str] = mapped_column(String)


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    slug: Mapped[str] = mapped_column(String, unique=True)
    movies: Mapped[List["Movie"]] = relationship(
        secondary=movie_categories,
        back_populates="categories",
        passive_deletes=True,
    )


class Movie(Base):
    __tablename__ = "movies"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String, index=True)
    original_title: Mapped[Optional[str]] = mapped_column(String)
    file_id: Mapped[str] = mapped_column(String)
    description: Mapped[Optional[str]] = mapped_column(String)
    poster_url: Mapped[Optional[str]] = mapped_column(String)
    backdrop_url: Mapped[Optional[str]] = mapped_column(String)
    release_year: Mapped[Optional[int]] = mapped_column(Integer)
    duration_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    rating: Mapped[Optional[float]] = mapped_column(Float)
    views: Mapped[int] = mapped_column(Integer, default=0)
    size_bytes: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[Optional[str]] = mapped_column(String)

    categories: Mapped[List["Category"]] = relationship(
        secondary=movie_categories,
        back_populates="movies",
        passive_deletes=True,
    )


class WatchHistory(Base):
    __tablename__ = "watch_history"
    __table_args__ = (
        UniqueConstraint("user_telegram_id", "movie_id", name="uq_watch_history_user_movie"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_telegram_id: Mapped[str] = mapped_column(String, index=True)
    movie_id: Mapped[int] = mapped_column(Integer, ForeignKey("movies.id", ondelete="CASCADE"), index=True)
    progress_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    duration_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    watch_count: Mapped[int] = mapped_column(Integer, default=1)
    last_watched_at: Mapped[str] = mapped_column(String)

    movie: Mapped["Movie"] = relationship("Movie", lazy="joined", passive_deletes=True)
