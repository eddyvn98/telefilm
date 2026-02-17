import os
import asyncio
from telethon import TelegramClient

# Import settings
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))
from backend.core.config import get_settings

settings = get_settings()

async def main():
    client = TelegramClient('diag_session', settings.API_ID, settings.API_HASH)
    await client.start(bot_token=settings.BOT_TOKEN)
    
    print("--- Dialogs List ---")
    async for dialog in client.iter_dialogs():
        print(f"Name: {dialog.name} | ID: {dialog.id} | Type: {type(dialog.entity)}")
    print("--------------------")
    
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
