import logging
import os

from sqlalchemy import delete, select

from ..core.database import AsyncSessionLocal
from ..core.models import Movie, WatchHistory, movie_categories
from ..core.paths import resolve_media_url
from ..core.utils import normalize_title
from .telegram_client import TelegramClientService

logger = logging.getLogger(__name__)


class MovieCleanerService:
    def __init__(self):
        self.tg_service = TelegramClientService.get_instance()

    @staticmethod
    def _parse_ref(file_id: str | None):
        if not file_id or ":" not in file_id:
            return None
        try:
            channel, message = file_id.split(":", 1)
            return int(channel), int(message)
        except ValueError:
            return None

    @staticmethod
    def _remove_local_media(urls: list[str | None]) -> int:
        removed = 0
        for url in urls:
            path = resolve_media_url(url)
            if not path:
                continue
            try:
                os.remove(path)
                removed += 1
            except FileNotFoundError:
                pass
            except OSError as exc:
                logger.warning("Failed to remove media %s: %s", path, exc)
        return removed

    async def delete_movie(self, movie_id: int) -> dict:
        async with AsyncSessionLocal() as db:
            movie = await db.scalar(select(Movie).where(Movie.id == movie_id))
            if not movie:
                return {"found": False, "db_deleted": 0, "telegram_deleted": 0, "files_deleted": 0, "errors": []}

            file_ref = self._parse_ref(movie.file_id)
            media_urls = [movie.poster_url, movie.backdrop_url]
            title = movie.title
            try:
                await db.execute(delete(WatchHistory).where(WatchHistory.movie_id == movie_id))
                await db.execute(movie_categories.delete().where(movie_categories.c.movie_id == movie_id))
                await db.delete(movie)
                await db.commit()
            except Exception:
                await db.rollback()
                raise

        result = {
            "found": True,
            "title": title,
            "db_deleted": 1,
            "telegram_deleted": 0,
            "files_deleted": 0,
            "errors": [],
        }

        if file_ref:
            try:
                await self.tg_service.start()
                if await self.tg_service.delete_message(*file_ref):
                    result["telegram_deleted"] = 1
                else:
                    result["errors"].append("Telegram cleanup failed")
            except Exception as exc:
                logger.warning("Remote cleanup failed for movie %s: %s", movie_id, exc)
                result["errors"].append(f"Telegram cleanup failed: {exc}")

        result["files_deleted"] = self._remove_local_media(media_urls)
        return result

    async def clean_duplicates(self):
        async with AsyncSessionLocal() as db:
            movies = (await db.execute(select(Movie))).scalars().all()

        groups = {}
        for movie in movies:
            groups.setdefault(normalize_title(movie.title), []).append(movie.id)

        duplicate_ids = []
        for ids in groups.values():
            if len(ids) > 1:
                ids.sort(reverse=True)
                duplicate_ids.extend(ids[1:])

        summary = {
            "total_indexed": len(movies),
            "unique_titles": len(groups),
            "duplicates_found": len(duplicate_ids),
            "telegram_deleted": 0,
            "files_deleted": 0,
            "db_deleted": 0,
            "errors": [],
        }

        for movie_id in duplicate_ids:
            try:
                result = await self.delete_movie(movie_id)
                summary["telegram_deleted"] += result["telegram_deleted"]
                summary["files_deleted"] += result["files_deleted"]
                summary["db_deleted"] += result["db_deleted"]
                summary["errors"].extend(result["errors"])
            except Exception as exc:
                logger.exception("Duplicate cleanup failed for movie %s", movie_id)
                summary["errors"].append(f"Movie {movie_id}: {exc}")

        return summary
