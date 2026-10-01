import asyncio
import hashlib
import logging
import math
import os
import random
import time
from datetime import datetime, timezone

from sqlalchemy import select
from telethon.tl.functions.upload import SaveBigFilePartRequest, SaveFilePartRequest
from telethon.tl.types import InputFile, InputFileBig

from ..core.config import get_settings
from ..core.database import AsyncSessionLocal
from ..core.models import Movie
from ..core.paths import is_upload_path_allowed
from ..core.utils import normalize_title
from .telegram_client import TelegramClientService
from .thumbnail_service import ThumbnailService

logger = logging.getLogger(__name__)
settings = get_settings()
VIDEO_EXTENSIONS = (".mp4", ".mkv", ".avi", ".ts", ".mov", ".m4v")


class UploadService:
    _instance = None

    def __init__(self):
        self.is_uploading = False
        self.progress = {"current_file": "", "status": "Idle", "percent": 0, "speed_mb": 0}
        self.tg_service = TelegramClientService.get_instance()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @staticmethod
    def _collect_files(path: str) -> list[str]:
        if os.path.isfile(path):
            return [path]
        if not os.path.isdir(path):
            return []
        found = []
        for root, _, files in os.walk(path, followlinks=False):
            for name in files:
                found.append(os.path.join(root, name))
        return found

    async def _upload_throttled(self, client, file_path: str, callback):
        limit_mb = float(settings.UPLOAD_SPEED_LIMIT_MB or 0)
        if limit_mb <= 0:
            return await client.upload_file(
                file_path,
                part_size_kb=512,
                progress_callback=callback,
            )

        file_size = os.path.getsize(file_path)
        part_size = 512 * 1024
        total_parts = math.ceil(file_size / part_size)
        file_id = random.getrandbits(63)
        is_big = file_size > 10 * 1024 * 1024
        md5 = hashlib.md5()
        sent = 0
        started = time.monotonic()
        bytes_per_second = limit_mb * 1024 * 1024

        with open(file_path, "rb") as handle:
            for part_index in range(total_parts):
                data = handle.read(part_size)
                if not data:
                    break
                if not is_big:
                    md5.update(data)

                if is_big:
                    ok = await client(
                        SaveBigFilePartRequest(
                            file_id=file_id,
                            file_part=part_index,
                            file_total_parts=total_parts,
                            bytes=data,
                        )
                    )
                else:
                    ok = await client(
                        SaveFilePartRequest(
                            file_id=file_id,
                            file_part=part_index,
                            bytes=data,
                        )
                    )
                if not ok:
                    raise RuntimeError(f"Telegram rejected upload part {part_index}")

                sent += len(data)
                callback(sent, file_size)
                expected_elapsed = sent / bytes_per_second
                delay = expected_elapsed - (time.monotonic() - started)
                if delay > 0:
                    await asyncio.sleep(delay)

        name = os.path.basename(file_path)
        if is_big:
            return InputFileBig(id=file_id, parts=total_parts, name=name)
        return InputFile(id=file_id, parts=total_parts, name=name, md5_checksum=md5.hexdigest())

    async def _is_duplicate(self, file_name: str, file_path: str) -> bool:
        current_size = os.path.getsize(file_path)
        normalized = normalize_title(file_name)
        async with AsyncSessionLocal() as db:
            exact = await db.scalar(select(Movie.id).where(Movie.title == file_name))
            if exact:
                return True
            rows = (await db.execute(select(Movie.title, Movie.size_bytes))).all()
        return any(
            normalize_title(title) == normalized
            and abs((size_bytes or 0) - current_size) < 1024
            for title, size_bytes in rows
        )

    async def _generate_media(self, file_path: str, file_name: str) -> tuple[str, str, str, str] | None:
        file_size = os.path.getsize(file_path)
        digest = hashlib.sha256(f"{os.path.realpath(file_path)}:{file_size}".encode()).hexdigest()[:10]
        base = "".join(ch if ch.isalnum() else "_" for ch in file_name.rsplit(".", 1)[0])[:120]
        safe_name = f"{base}_{digest}"
        poster_path = os.path.join("frontend", "static", "thumbnails", f"{safe_name}_poster.jpg")
        backdrop_path = os.path.join("frontend", "static", "backdrops", f"{safe_name}_back.jpg")

        poster_ok = await asyncio.to_thread(
            ThumbnailService.generate_thumbnail,
            file_path,
            poster_path,
            "00:00:05",
        )
        backdrop_ok = await asyncio.to_thread(
            ThumbnailService.generate_thumbnail,
            file_path,
            backdrop_path,
            "00:00:45",
        )
        if not backdrop_ok:
            backdrop_ok = await asyncio.to_thread(
                ThumbnailService.generate_thumbnail,
                file_path,
                backdrop_path,
                "00:00:05",
            )
        if not poster_ok or not backdrop_ok:
            for path in (poster_path, backdrop_path):
                try:
                    if os.path.exists(path):
                        os.remove(path)
                except OSError:
                    pass
            return None

        return (
            poster_path,
            backdrop_path,
            f"/static/thumbnails/{safe_name}_poster.jpg",
            f"/static/backdrops/{safe_name}_back.jpg",
        )

    async def _process_file(self, client, target_entity, target_channel_id: int, file_path: str) -> None:
        if not is_upload_path_allowed(file_path):
            logger.warning("Skipping path outside UPLOAD_ROOTS: %s", file_path)
            return
        if not file_path.lower().endswith(VIDEO_EXTENSIONS):
            return

        file_name = os.path.basename(file_path)
        self.progress.update({"current_file": file_name, "status": "Checking database...", "percent": 0})
        if await self._is_duplicate(file_name, file_path):
            logger.info("Skipping duplicate: %s", file_name)
            return

        media = await self._generate_media(file_path, file_name)
        if not media:
            self.progress["status"] = f"Skipped {file_name} (thumbnail failed)"
            logger.error("Thumbnail generation failed: %s", file_name)
            return
        poster_path, backdrop_path, poster_url, backdrop_url = media

        last_update = [time.monotonic()]
        last_bytes = [0]

        def progress_callback(current, total):
            now = time.monotonic()
            self.progress["percent"] = int((current / max(total, 1)) * 100)
            elapsed = now - last_update[0]
            if elapsed >= 1:
                speed = ((current - last_bytes[0]) / elapsed) / (1024 * 1024)
                self.progress["speed_mb"] = round(speed, 2)
                last_update[0] = now
                last_bytes[0] = current
            self.progress["status"] = (
                f"Uploading {file_name}... {self.progress['percent']}% "
                f"({self.progress['speed_mb']} MB/s)"
            )

        message = None
        try:
            self.progress["status"] = f"Uploading {file_name} to Telegram..."
            input_file = await self._upload_throttled(client, file_path, progress_callback)
            message = await client.send_file(
                target_entity,
                input_file,
                caption=f"File: {file_name}",
            )
            file_id = f"{target_channel_id}:{message.id}"
            file_size = os.path.getsize(file_path)

            try:
                async with AsyncSessionLocal() as db:
                    db.add(
                        Movie(
                            title=file_name,
                            file_id=file_id,
                            poster_url=poster_url,
                            backdrop_url=backdrop_url,
                            release_year=datetime.now(timezone.utc).year,
                            rating=0.0,
                            size_bytes=file_size,
                            created_at=datetime.now(timezone.utc).isoformat(),
                        )
                    )
                    await db.commit()
            except Exception:
                if message:
                    await self.tg_service.delete_message(target_channel_id, message.id)
                raise

            logger.info("Uploaded and indexed: %s", file_name)
        except Exception:
            for path in (poster_path, backdrop_path):
                try:
                    if os.path.exists(path):
                        os.remove(path)
                except OSError:
                    pass
            raise

    async def scan_and_upload(self, directory: str):
        if self.is_uploading:
            logger.info("Upload already in progress")
            return

        self.is_uploading = True
        self.progress.update({"status": "Started", "percent": 0, "speed_mb": 0})
        try:
            await self.tg_service.start()
            client = self.tg_service.client
            target_channel_id = int(settings.STORAGE_CHANNEL_ID)
            if (
                target_channel_id < 0
                and target_channel_id > -10000000000
                and not str(target_channel_id).startswith("-100")
            ):
                target_channel_id = int("-100" + str(target_channel_id)[1:])

            target_entity = await client.get_entity(target_channel_id)
            files = await asyncio.to_thread(self._collect_files, directory)
            logger.info("Found %d filesystem entries under scan path", len(files))

            errors = 0
            for file_path in files:
                try:
                    await self._process_file(client, target_entity, target_channel_id, file_path)
                except Exception as exc:
                    errors += 1
                    logger.exception("Upload failed for %s: %s", file_path, exc)
                    self.progress["status"] = f"Error on {os.path.basename(file_path)}"
                    continue

            self.progress["status"] = "Completed" if errors == 0 else f"Completed with {errors} error(s)"
            self.progress["current_file"] = ""
        except Exception as exc:
            logger.exception("Fatal scan/upload error: %s", exc)
            self.progress["status"] = f"Error: {exc}"
        finally:
            self.is_uploading = False

    def get_status(self):
        return {"is_uploading": self.is_uploading, "progress": dict(self.progress)}
