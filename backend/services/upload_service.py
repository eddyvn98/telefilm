import os
import asyncio
import logging
from telethon import TelegramClient
from sqlalchemy import select
from ..core.config import get_settings
from ..core.models import Movie
from ..core.database import AsyncSessionLocal
from .telegram_client import TelegramClientService

logger = logging.getLogger(__name__)
settings = get_settings()

class UploadService:
    _instance = None
    
    def __init__(self):
        self.is_uploading = False
        self.progress = {"current_file": "", "status": "Idle"}
        self.tg_service = TelegramClientService.get_instance()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def scan_and_upload(self, directory: str):
        print(f"DEBUG: scan_and_upload started for {directory}", flush=True)
        if self.is_uploading:
            logger.info("Upload already in progress, skipping.")
            print("DEBUG: Already uploading inside service", flush=True)
            return
        
        self.is_uploading = True
        self.progress["status"] = "Started"
        print("DEBUG: Set is_uploading to True", flush=True)
        
        try:
            logger.info("Initializing Telegram service...")
            await self.tg_service.start()
            client = self.tg_service.client
            target_channel_id = int(settings.STORAGE_CHANNEL_ID)
            
            logger.info(f"Resolving storage channel ID: {target_channel_id}")
            # Auto-fix IDs missing -100 prefix (common for Supergroups/Channels)
            if target_channel_id < 0 and target_channel_id > -10000000000 and not str(target_channel_id).startswith("-100"):
                fixed_id = int("-100" + str(target_channel_id)[1:])
                logger.warning(f"⚠️ Channel ID {target_channel_id} looks like a Supergroup missing -100 prefix. Trying {fixed_id}")
                target_channel_id = fixed_id

            # Resolve the target entity once at the start. 
            try:
                target_entity = await client.get_entity(target_channel_id)
                entity_name = getattr(target_entity, 'title', getattr(target_entity, 'first_name', str(target_entity.id)))
                logger.info(f"✅ Resolved target: {entity_name} ({type(target_entity).__name__})")
            except Exception as e:
                logger.error(f"❌ Could not resolve target channel {target_channel_id}: {e}")
                raise ValueError(f"Target channel resolution failed: {e}")

            # Support both directory and single file
            logger.info(f"Processing path: {directory}")
            files_to_process = []
            if os.path.isfile(directory):
                files_to_process.append((os.path.dirname(directory), os.path.basename(directory)))
            elif os.path.isdir(directory):
                for root, _, files in os.walk(directory):
                    for file in files:
                        files_to_process.append((root, file))
            else:
                logger.error(f"Path not found: {directory}")
                raise ValueError(f"Path not found: {directory}")

            logger.info(f"Found {len(files_to_process)} files to check.")
            for root, file in files_to_process:
                # Expanded support for more video formats including .ts
                if file.lower().endswith(('.mp4', '.mkv', '.avi', '.ts', '.mov', '.m4v')):
                    file_path = os.path.join(root, file)
                    logger.info(f"Processing file: {file}")
                    self.progress["current_file"] = file
                    self.progress["status"] = "Checking database..."
                    
                    async with AsyncSessionLocal() as db:
                        existing = await db.execute(select(Movie).where(Movie.title == file))
                        if existing.scalar_one_or_none():
                            logger.info(f"File already in database: {file}")
                            continue

                    self.progress["status"] = f"Uploading {file} to Telegram..."
                    self.progress["percent"] = 0
                    self.progress["speed_mb"] = 0
                    
                    import time
                    import math
                    from telethon.tl.functions.upload import SaveBigFilePartRequest
                    from telethon.tl.types import InputFileBig

                    async def upload_file_fast(client, file_path, progress_callback):
                        logger.info(f"Starting FastUploader for: {file_path}")
                        file_size = os.path.getsize(file_path)
                        part_size = 512 * 1024  # 512KB per part
                        parts_count = math.ceil(file_size / part_size)
                        
                        file_id = int.from_bytes(os.urandom(8), 'big')
                        semaphore = asyncio.Semaphore(8)
                        
                        start_time = time.time()
                        last_update_time = [start_time]

                        async def upload_part(part_index):
                            async with semaphore:
                                offset = part_index * part_size
                                
                                # Read data in a thread to avoid blocking the event loop
                                def read_data():
                                    with open(file_path, 'rb') as f:
                                        f.seek(offset)
                                        return f.read(part_size)
                                
                                data = await asyncio.to_thread(read_data)
                                
                                await client(SaveBigFilePartRequest(
                                    file_id=file_id,
                                    file_part=part_index,
                                    file_total_parts=parts_count,
                                    bytes=data
                                ))
                                
                                if progress_callback:
                                    current_sent = (part_index + 1) * part_size
                                    if current_sent > file_size: current_sent = file_size
                                    
                                    now = time.time()
                                    if now - last_update_time[0] >= 1.0:
                                        progress_callback(current_sent, file_size)
                                        last_update_time[0] = now

                        print(f"DEBUG: Starting {parts_count} upload tasks...", flush=True)
                        tasks = [upload_part(i) for i in range(parts_count)]
                        await asyncio.gather(*tasks)
                        
                        return InputFileBig(
                            id=file_id,
                            parts=parts_count,
                            name=os.path.basename(file_path)
                        )

                    # Update status display for the frontend
                    last_update = [time.time()]
                    bytes_last = [0]
                    def wrapped_callback(current, total):
                        now = time.time()
                        self.progress["percent"] = int((current / total) * 100)
                        if now - last_update[0] >= 1.0:
                            diff = current - bytes_last[0]
                            speed = (diff / (now - last_update[0])) / (1024 * 1024)
                            self.progress["speed_mb"] = round(speed, 2)
                            last_update[0] = now
                            bytes_last[0] = current
                        self.progress["status"] = f"Uploading {file}... {self.progress['percent']}% ({self.progress['speed_mb']} MB/s)"

                    # 1. Generate Metadata (Thumbnails/Previews)
                    from .thumbnail_service import ThumbnailService
                    thumb_dir = os.path.join("frontend", "static", "thumbnails")
                    back_dir = os.path.join("frontend", "static", "backdrops")
                    
                    # Safe filenames
                    safe_name = "".join([c if c.isalnum() else "_" for c in file.rsplit('.', 1)[0]])
                    poster_path = os.path.join(thumb_dir, f"{safe_name}_poster.jpg")
                    backdrop_path = os.path.join(back_dir, f"{safe_name}_back.jpg")
                    
                    # Generate locally if possible
                    print(f"DEBUG: Generating thumbnails for {file}...", flush=True)
                    ThumbnailService.generate_thumbnail(file_path, poster_path, timestamp="00:00:05")
                    ThumbnailService.generate_thumbnail(file_path, backdrop_path, timestamp="00:00:45")
                    
                    # DB paths (browser-accessible)
                    poster_url = f"/static/thumbnails/{safe_name}_poster.jpg"
                    backdrop_url = f"/static/backdrops/{safe_name}_back.jpg"

                    logger.info("Executing parallel upload...")
                    input_file = await upload_file_fast(client, file_path, wrapped_callback)
                    
                    logger.info("Sending InputFile to Telegram...")
                    message = await client.send_file(
                        target_entity,
                        input_file,
                        caption=f"File: {file}"
                    )
                        
                    file_id_str = f"{target_channel_id}:{message.id}"
                    logger.info(f"✅ Upload succeeded. Message ID: {message.id}")
                    
                    async with AsyncSessionLocal() as db:
                        movie = Movie(
                            title=file,
                            file_id=file_id_str,
                            poster_url=poster_url,
                            backdrop_url=backdrop_url,
                            release_year=2024,
                            rating=0.0
                        )
                        db.add(movie)
                        await db.commit()
                        logger.info("✅ Database updated.")
            
            self.progress["status"] = "Completed"
            self.progress["current_file"] = ""
            logger.info("🏁 Scan and upload process finished successfully.")
        except Exception as e:
            logger.exception(f"💥 Fatal error in scan_and_upload: {e}")
            self.progress["status"] = f"Error: {str(e)}"
        finally:
            self.is_uploading = False

    def get_status(self):
        return {
            "is_uploading": self.is_uploading,
            "progress": self.progress
        }
