import asyncio
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
import os
import sys
import getpass

# Thêm thư mục hiện tại vào path để load config
sys.path.append(os.getcwd())
from backend.core.config import get_settings

async def main():
    settings = get_settings()
    
    print("="*60)
    print("🚀 TELEGRAM USER LOGIN UTILITY (Manual Mode)")
    print("="*60)
    print(f"API_ID: {settings.API_ID}")
    print(f"API_HASH: {settings.API_HASH}")
    print("-"*60)
    
    session_name = 'user_session'
    client = TelegramClient(
        session_name, 
        settings.API_ID, 
        settings.API_HASH,
        device_model='PC 64bit',
        system_version='Windows 10',
        app_version='4.10.2'
    )
    
    print("Đang kết nối tới Telegram...")
    await client.connect()
    
    if not await client.is_user_authorized():
        phone = input("Sếp nhập số điện thoại (ví dụ +84932690949): ")
        await client.send_code_request(phone)
        
        code = input("Sếp nhập mã xác nhận từ Telegram: ")
        try:
            await client.sign_in(phone, code)
        except SessionPasswordNeededError:
            print("\n🔐 TÀI KHOẢN CỦA SẾP CÓ MẬT KHẨU 2 LỚP (2FA)")
            print("LƯU Ý: Khi nhập mật khẩu, các ký tự sẽ KHÔNG HIỂN THỊ (để bảo mật).")
            print("Sếp cứ gõ đúng rồi nhấn Enter là được ạ.")
            password = getpass.getpass("Mật khẩu 2FA của sếp: ")
            await client.sign_in(password=password)
            
    me = await client.get_me()
    print(f"\n✅ ĐÃ ĐĂNG NHẬP THÀNH CÔNG!")
    print(f"User: {me.first_name} (@{me.username if me.username else 'N/A'})")
    print(f"File session đã được lưu: {session_name}.session")
    
    await client.disconnect()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nĐã hủy bởi người dùng.")
    except Exception as e:
        print(f"\n\n❌ LỖI: {e}")
