import asyncio
import sys

from backend.core.paths import validate_upload_path
from backend.services.telegram_client import TelegramClientService
from backend.services.upload_service import UploadService


async def main(path: str):
    safe_path = validate_upload_path(path)
    service = UploadService.get_instance()
    await service.scan_and_upload(safe_path)
    print(service.get_status()["progress"]["status"])
    await TelegramClientService.get_instance().stop()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python upload_to_telegram.py <allowed_file_or_directory>")
    asyncio.run(main(sys.argv[1]))
