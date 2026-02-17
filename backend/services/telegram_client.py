import logging
from telethon import TelegramClient
from ..core.config import get_settings
import asyncio

settings = get_settings()
logger = logging.getLogger(__name__)

class TelegramClientService:
    _instance = None
    
    def __init__(self):
        import os
        if not settings.API_ID or not settings.API_HASH:
            logger.warning("API_ID or API_HASH not set. Streaming will fail.")
            
        # Check for user session first (allows large uploads)
        session_path = 'user_session.session'
        if os.path.exists(session_path):
            logger.info("Using existing USER session for Telegram")
            self.session_name = 'user_session'
            self.is_user = True
        else:
            logger.info("Using BOT session for Telegram")
            self.session_name = 'bot_session'
            self.is_user = False

        self.client = TelegramClient(
            self.session_name, 
            settings.API_ID, 
            settings.API_HASH,
            device_model='PC 64bit',
            system_version='Windows 10',
            app_version='4.10.2'
        )
        self.started = False

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def start(self):
        if not self.started:
            if self.is_user:
                # User sessions are started without token if session file exists and is authorized
                await self.client.start()
            else:
                await self.client.start(bot_token=settings.BOT_TOKEN)
            
            self.started = True
            me = await self.client.get_me()
            logger.info(f"Telegram Client Started: {getattr(me, 'username', 'Unknown')}")

    async def get_file_stream(self, channel_id: int, message_id: int, offset: int = 0, limit: int = None):
        """
        Stream a file from a message in a channel.
        offset: Byte offset to start stream from.
        limit: Number of bytes to read (chunk size).
        """
        try:
            print(f"DEBUG: TG Client getting message {message_id} from {channel_id}", flush=True)
            message = await self.client.get_messages(channel_id, ids=message_id)
            if not message or not message.file:
                print(f"ERROR: Message {message_id} not found or no file", flush=True)
                raise ValueError("Message not found or has no file")
            
            print(f"DEBUG: Starting download iteration for {message.file.name} ({message.file.size} bytes)", flush=True)
            # Telethon's iter_download handles offset/limit
            # chunk_size is implementation detail, typically 128KB - 1MB
            count = 0
            async for chunk in self.client.iter_download(message.media, offset=offset, limit=limit, chunk_size=1024*1024):
                if count == 0:
                    print(f"DEBUG: Yielding FIRST chunk of size {len(chunk)}", flush=True)
                yield chunk
                count += 1
            print(f"DEBUG: Stream finished, yielded {count} chunks", flush=True)
                
        except Exception as e:
            print(f"ERROR in get_file_stream: {e}", flush=True)
            logger.error(f"Error streaming file: {e}")
            raise

    async def get_file_size(self, channel_id: int, message_id: int) -> int:
        message = await self.client.get_messages(channel_id, ids=message_id)
        if message and message.file:
            return message.file.size
        return 0

    async def stop(self):
        if self.started:
            await self.client.disconnect()
            self.started = False
            logger.info("Telegram Client Stopped")

