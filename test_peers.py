import asyncio
from telethon import TelegramClient
from telethon.tl.types import PeerChannel, InputPeerChannel
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
    
    raw_id = -3749586011 # Original
    fixed_id = -1003749586011 # With prefix
    positive_id = 3749586011
    
    tests = [
        ("Original ID", raw_id),
        ("Fixed ID (-100)", fixed_id),
        ("Positive ID", positive_id),
        ("PeerChannel(fixed)", PeerChannel(fixed_id)),
        ("PeerChannel(positive)", PeerChannel(positive_id)),
    ]
    
    with open("peer_results.txt", "w", encoding="utf-8") as out:
        for name, tid in tests:
            try:
                out.write(f"Testing {name}: {tid}\n")
                out.flush()
                entity = await client.get_entity(tid)
                out.write(f"✅ Success! Entity: {getattr(entity, 'title', str(entity.id))} | Type: {type(entity).__name__}\n")
                out.flush()
                break
            except Exception as e:
                out.write(f"❌ Failed: {e}\n")
                out.flush()
    
    await client.disconnect()
    print("DONE. Check peer_results.txt")

if __name__ == "__main__":
    asyncio.run(main())
