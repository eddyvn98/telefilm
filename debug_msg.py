import asyncio
import os
from telethon import TelegramClient
from dotenv import load_dotenv

load_dotenv()

async def debug_file():
    api_id = os.getenv("API_ID")
    api_hash = os.getenv("API_HASH")
    channel_id = -1003749586011
    message_id = 4
    
    client = TelegramClient('user_session', api_id, api_hash)
    await client.connect()
    
    if not await client.is_user_authorized():
        print("❌ Not authorized!")
        return

    print(f"✅ Authorized. Getting message {message_id} from {channel_id}...")
    try:
        msg = await client.get_messages(channel_id, ids=message_id)
        if msg:
            print(f"✅ Message found: {msg.text[:50]}...")
            if msg.file:
                print(f"📎 Message has file: {msg.file.name}, size: {msg.file.size} bytes")
            else:
                print("❌ Message has NO file!")
        else:
            print("❌ Message NOT found!")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(debug_file())
