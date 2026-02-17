import os
import asyncio
import logging
import math
import time
print("--- SCRIPT STARTED ---")
from telethon import TelegramClient
from telethon.tl.functions.upload import SaveBigFilePartRequest
from telethon.tl.types import InputFileBig

# Import settings
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))
from backend.core.config import get_settings

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

settings = get_settings()

async def upload_file_fast(client, file_path):
    file_size = os.path.getsize(file_path)
    part_size = 512 * 1024  # 512KB per part
    parts_count = math.ceil(file_size / part_size)
    
    file_id = int.from_bytes(os.urandom(8), 'big')
    
    # Semaphore to limit parallel uploads
    semaphore = asyncio.Semaphore(8) # 8 parallel parts
    
    start_time = time.time()
    last_update = [start_time]
    bytes_sent_total = [0]

    async def upload_part(part_index):
        async with semaphore:
            offset = part_index * part_size
            with open(file_path, 'rb') as f:
                f.seek(offset)
                data = f.read(part_size)
            
            await client(SaveBigFilePartRequest(
                file_id=file_id,
                file_part=part_index,
                file_total_parts=parts_count,
                bytes=data
            ))
            
            bytes_sent_total[0] += len(data)
            now = time.time()
            if now - last_update[0] >= 1.0:
                percent = int((bytes_sent_total[0] / file_size) * 100)
                speed = (bytes_sent_total[0] / (now - start_time)) / (1024 * 1024)
                logger.info(f"Progress: {percent}% | Speed: {speed:.2f} MB/s")
                last_update[0] = now

    tasks = [upload_part(i) for i in range(parts_count)]
    await asyncio.gather(*tasks)
    
    return InputFileBig(
        id=file_id,
        parts=parts_count,
        name=os.path.basename(file_path)
    )

async def main():
    file_path = r"H:\bestpretty\Processed\ADN-057 Tôi muốn được yêu bởi bạn. Ishihara Rina - Miss_highlight.mp4"
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return

    print(f"Connecting with IN-MEMORY session...")
    client = TelegramClient(None, settings.API_ID, settings.API_HASH, connection_retries=3, retry_delay=1)
    print("Starting client...")
    try:
        await asyncio.wait_for(client.start(bot_token=settings.BOT_TOKEN), timeout=15)
        print("Client started.")
    except asyncio.TimeoutError:
        print("❌ Client start TIMEOUT")
        return
    except Exception as e:
        print(f"❌ Client start ERROR: {e}")
        return
    
    target_channel_id = int(settings.STORAGE_CHANNEL_ID)
    # Ensure -100 prefix
    if target_channel_id < 0 and target_channel_id > -10000000000:
        target_channel_id = int("-100" + str(target_channel_id)[1:])
    
    print(f"Target Channel ID: {target_channel_id}")
    try:
        print("Resolving entity...")
        target_entity = await client.get_entity(target_channel_id)
        print(f"Entity resolved: {type(target_entity)}")
        logger.info(f"Resolved Entity Details: {target_entity}")

        logger.info(f"Starting fast upload for: {file_path}")
        # Try a safe name (ASCII only) for the input_file to rule out encoding issues
        safe_name = "debug_video.mp4" 
        input_file = await upload_file_fast(client, file_path)
        input_file.name = safe_name # Override for safety
        
        logger.info(f"Finishing upload (sending to {type(target_entity)})...")
        # Explicitly check if it's a channel or chat
        from telethon.tl.types import Channel, Chat
        if isinstance(target_entity, Channel):
            logger.info("Target is a CHANNEL/SUPERGROUP.")
        elif isinstance(target_entity, Chat):
            logger.info("Target is a BASIC CHAT (Group).")
        
        message = await client.send_file(
            target_entity,
            input_file,
            caption=f"Debug Upload: {os.path.basename(file_path)}"
        )
        logger.info(f"✅ Upload successful! Message ID: {message.id}")

    except Exception as e:
        logger.exception(f"❌ Upload failed with error: {e}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
