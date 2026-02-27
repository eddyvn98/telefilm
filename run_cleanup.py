import asyncio
import os
import sys

# Adjust path to import backend modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from backend.services.movie_cleaner_service import MovieCleanerService
from backend.services.telegram_client import TelegramClientService

async def main():
    print("🚀 Bắt đầu quá trình dọn dẹp phim trùng lặp (Smart Clean)...")
    cleaner = MovieCleanerService()
    summary = await cleaner.clean_duplicates()
    
    print("\n✅ Hoàn tất dọn dẹp!")
    print(f"   - Tổng số phim ban đầu: {summary['total_indexed']}")
    print(f"   - Số phim duy nhất (sau khi chuẩn hóa tên): {summary['unique_titles']}")
    print(f"   - Số bản trùng tìm thấy: {summary['duplicates_found']}")
    print(f"   - Đã xóa trên Telegram: {summary['telegram_deleted']}")
    print(f"   - Đã xóa DB: {summary['db_deleted']}")
    
    if summary['errors']:
        print("\n⚠️ Một số lỗi xảy ra:")
        for error in summary['errors'][:5]:
            print(f"   - {error}")
            
    # Stop TG service
    await TelegramClientService.get_instance().stop()

if __name__ == "__main__":
    asyncio.run(main())
