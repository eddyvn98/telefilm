import os
import logging
import re
from sqlalchemy import select
from ..core.database import AsyncSessionLocal
from ..core.models import Movie, movie_categories
from ..core.utils import normalize_title
from .telegram_client import TelegramClientService

logger = logging.getLogger(__name__)

class MovieCleanerService:
    def __init__(self):
        self.tg_service = TelegramClientService.get_instance()

    # normalize_title moved to backend.core.utils

    async def clean_duplicates(self):
        """
        Smart cleanup: finds duplicates based on normalized titles.
        If titles are identical after normalization, they are considered duplicates.
        We keep the one with the highest ID (usually the most recent/complete one).
        """
        await self.tg_service.start()
        
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Movie))
            movies = result.scalars().all()
            
            # Map: normalized_title -> list of movie objects
            groups = {}
            for m in movies:
                norm = normalize_title(m.title)
                if norm not in groups:
                    groups[norm] = []
                groups[norm].append(m)
            
            to_delete = []
            for norm, items in groups.items():
                if len(items) > 1:
                    # Sort by ID descending, keep the first one, delete the rest
                    items.sort(key=lambda x: x.id, reverse=True)
                    to_delete.extend(items[1:])
            
            summary = {
                "total_indexed": len(movies),
                "unique_titles": len(groups),
                "duplicates_found": len(to_delete),
                "telegram_deleted": 0,
                "files_deleted": 0,
                "db_deleted": 0,
                "errors": []
            }
            
            for movie in to_delete:
                m_id = movie.id
                m_title = movie.title
                
                # 1. Telegram cleanup
                try:
                    if movie.file_id and ":" in movie.file_id:
                        parts = movie.file_id.split(":")
                        cid, mid = int(parts[0]), int(parts[1])
                        if await self.tg_service.delete_message(cid, mid):
                            summary["telegram_deleted"] += 1
                except Exception as e:
                    logger.error(f"TG delete error for {m_id}: {e}")
                    summary["errors"].append(f"TG Error ({m_title}): {str(e)}")

                # 2. Local files cleanup
                try:
                    for url in [movie.poster_url, movie.backdrop_url]:
                        if url and url.startswith("/static/"):
                            rel_path = "frontend" + url
                            file_path = os.path.join(os.getcwd(), rel_path)
                            if os.path.exists(file_path):
                                os.remove(file_path)
                                summary["files_deleted"] += 1
                except Exception as e:
                    logger.error(f"File delete error for {m_id}: {e}")

                # 3. Database cleanup
                try:
                    await db.execute(movie_categories.delete().where(movie_categories.c.movie_id == m_id))
                    await db.delete(movie)
                    summary["db_deleted"] += 1
                except Exception as e:
                    logger.error(f"DB delete error for {m_id}: {e}")
                    summary["errors"].append(f"DB Error ({m_title}): {str(e)}")
            
            await db.commit()
            return summary
