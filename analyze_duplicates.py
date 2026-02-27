import os
import asyncio
import json
from sqlalchemy import select
from backend.core.config import get_settings
from backend.core.models import Movie
from backend.core.database import AsyncSessionLocal

async def analyze_duplicates():
    print("🔍 Đang truy xuất danh sách phim từ database...")
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Movie))
        movies = result.scalars().all()
        
    print(f"📊 Tổng số phim trong DB: {len(movies)}")
    
    # Phân tích theo tiêu chí trùng (Title + Size)
    analysis = {} # (title, size) -> [list of IDs]
    
    for m in movies:
        key = f"{m.title} | {m.size_bytes} bytes"
        if key not in analysis:
            analysis[key] = []
        analysis[key].append({
            "id": m.id,
            "title": m.title,
            "size": m.size_bytes,
            "file_id": m.file_id,
            "created_at": m.created_at
        })
    
    # Lọc ra các nhóm có nhiều hơn 1 phim
    duplicates = {k: v for k, v in analysis.items() if len(v) > 1}
    
    print(f"⚠️ Tìm thấy {len(duplicates)} nhóm phim bị trùng lặp.\n")
    
    if duplicates:
        output_file = "duplicates_report.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(duplicates, f, ensure_ascii=False, indent=4)
        print(f"📄 Báo cáo chi tiết đã được lưu vào: {output_file}")
        
        for key, items in list(duplicates.items())[:5]: # Chỉ in 5 nhóm đầu
            print(f"--- Group: {key} ---")
            for item in items:
                print(f"  [ID: {item['id']}] Date: {item['created_at']}")
        if len(duplicates) > 5:
            print("...")
    else:
        print("✅ Không tìm thấy phim nào trùng khớp cả Tên và Kích thước.")
        
    # Tạo danh sách toàn bộ phim để người dùng lọc tay
    full_list_file = "all_movies_list.txt"
    with open(full_list_file, "w", encoding="utf-8") as f:
        for m in sorted(movies, key=lambda x: x.title):
            f.write(f"ID: {m.id} | Size: {m.size_bytes} | Title: {m.title}\n")
    print(f"📜 Danh sách toàn bộ phim (để lọc tay) đã lưu vào: {full_list_file}")

if __name__ == "__main__":
    asyncio.run(analyze_duplicates())
