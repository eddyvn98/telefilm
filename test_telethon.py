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
    client = TelegramClient(None, settings.API_ID, settings.API_HASH)
    await client.start(bot_token=settings.BOT_TOKEN)
    print("Connected!")
    me = await client.get_me()
    print(f"Bot name: {me.first_name}")
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
