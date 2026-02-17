import os
import asyncio
import logging
from telethon import TelegramClient

# Import settings
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))
from backend.core.config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
settings = get_settings()

async def main():
    client = TelegramClient('uploader_session', settings.API_ID, settings.API_HASH)
    await client.start(bot_token=settings.BOT_TOKEN)
    
    orig_id = int(settings.STORAGE_CHANNEL_ID)
    possible_ids = [orig_id]
    
    # If it's a 10-digit negative, try adding -100 prefix
    id_str = str(orig_id)
    if id_str.startswith('-') and len(id_str) == 11: # - followed by 10 digits
        new_id = int("-100" + id_str[1:])
        possible_ids.append(new_id)
    
    for tid in possible_ids:
        try:
            logger.info(f"Testing ID: {tid}")
            entity = await client.get_entity(tid)
            logger.info(f"✅ Success! Entity: {entity.title if hasattr(entity, 'title') else entity.id} | Type: {type(entity)}")
            
            # Try a tiny upload to confirm
            with open("test.txt", "w") as f: f.write("test")
            await client.send_file(entity, "test.txt")
            logger.info(f"✅ Send successful to {tid}")
            os.remove("test.txt")
            
            print(f"MATCH_FOUND:{tid}")
            break
        except Exception as e:
            logger.error(f"❌ Failed for {tid}: {e}")
    
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
