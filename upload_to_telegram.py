import os
import asyncio
import logging
from telethon import TelegramClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select

# Adjust path to import backend modules
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.core.config import get_settings
from backend.core.models import Movie, Category
from backend.core.database import Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

# Setup independent DB connection for script
engine = create_async_engine(settings.DATABASE_URL)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def upload_and_index(directory: str):
    if not settings.API_ID or not settings.API_HASH:
        logger.error("API_ID and API_HASH are required for uploading.")
        return

    client = TelegramClient('uploader_session', settings.API_ID, settings.API_HASH)
    await client.start(bot_token=settings.BOT_TOKEN) # Or user session if needed for large uploads? 
    # Note: Bots has 50MB upload limit. Users have 2GB.
    # To upload large movies, we MUST use a User Session (login as user), NOT Bot Token.
    # For this script, we assume the user might want to login interactively.
    # We will try to start as a user first.
    
    if not await client.is_user_authorized():
        logger.info("Client not authorized. Please login as a User (not Bot) to upload large files.")
        # This might trigger interactive login in terminal
        await client.start()

    # Ensure storage channel
    if not settings.STORAGE_CHANNEL_ID:
        logger.error("STORAGE_CHANNEL_ID is required.")
        return
        
    target_channel = int(settings.STORAGE_CHANNEL_ID)

    async with AsyncSessionLocal() as db:
        for root, _, files in os.walk(directory):
            for file in files:
                if file.lower().endswith(('.mp4', '.mkv', '.avi')):
                    file_path = os.path.join(root, file)
                    logger.info(f"Processing: {file}")
                    
                    # Check if already indexed (by title roughly)
                    # Real implementation should check hash or path
                    existing = await db.execute(select(Movie).where(Movie.title == file))
                    if existing.scalar_one_or_none():
                        logger.info("Skipping, already indexed.")
                        continue

                    # Upload
                    logger.info("Uploading to Telegram...")
                    
                    # Progress callback can be added
                    message = await client.send_file(
                        target_channel,
                        file_path,
                        caption=f"File: {file}",
                        attributes=[], # Add video attributes if possible
                        allow_cache=False,
                        part_size_kb=512
                    )
                    
                    file_id_str = f"{target_channel}:{message.id}"
                    logger.info(f"Uploaded. ID: {file_id_str}")
                    
                    # Create DB Entry
                    movie = Movie(
                        title=file,
                        file_id=file_id_str,
                        release_year=2024, # Placeholder
                        rating=0.0
                    )
                    db.add(movie)
                    await db.commit()
                    logger.info("Saved to DB.")

    await client.disconnect()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python upload_to_telegram.py <directory_to_scan>")
    else:
        asyncio.run(upload_and_index(sys.argv[1]))
