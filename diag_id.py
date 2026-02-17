import asyncio
from telethon import TelegramClient
import os
import sys

# Add current dir to path
sys.path.append(os.getcwd())
from backend.core.config import get_settings

async def main():
    settings = get_settings()
    print("Connecting...")
    client = TelegramClient('diag_bot_session', settings.API_ID, settings.API_HASH)
    await client.start(bot_token=settings.BOT_TOKEN)
    print("Connected!")
    
    target_id = int(settings.STORAGE_CHANNEL_ID)
    print(f"Target ID: {target_id}")
    
    try:
        print("Resolving entity...")
        entity = await client.get_entity(target_id)
        print(f"Success! Entity: {getattr(entity, 'title', str(entity.id))} | Type: {type(entity).__name__}")
        
        print("Testing tiny upload...")
        with open("diag_test.txt", "w") as f: f.write("Health Check")
        msg = await client.send_file(entity, "diag_test.txt", caption="Auto-Diagnostic Test")
        print(f"✅ Upload success! Message ID: {msg.id}")
        os.remove("diag_test.txt")
    except Exception as e:
        print(f"❌ Diagnostic failed: {e}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
