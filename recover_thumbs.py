import asyncio
import os
import sqlite3
from backend.services.thumbnail_service import ThumbnailService

async def recover_thumbnails():
    # For this to work, the local file must still exist
    # I'll check common paths
    local_dir = "D:\\CinemaProject" # The user said earlier it was here
    
    conn = sqlite3.connect('telegram_film.db')
    cur = conn.cursor()
    cur.execute("SELECT id, title FROM movies WHERE poster_url IS NULL")
    movies = cur.fetchall()
    
    for mid, title in movies:
        # Search for the local file
        found_path = None
        for root, _, files in os.walk(local_dir):
            if title in files:
                found_path = os.path.join(root, title)
                break
        
        if found_path:
            print(f"✅ Found local file for {title}: {found_path}")
            
            thumb_dir = os.path.join("frontend", "static", "thumbnails")
            back_dir = os.path.join("frontend", "static", "backdrops")
            
            safe_name = "".join([c if c.isalnum() else "_" for c in title.rsplit('.', 1)[0]])
            poster_path = os.path.join(thumb_dir, f"{safe_name}_poster.jpg")
            backdrop_path = os.path.join(back_dir, f"{safe_name}_back.jpg")
            
            ThumbnailService.generate_thumbnail(found_path, poster_path, timestamp="00:00:05")
            ThumbnailService.generate_thumbnail(found_path, backdrop_path, timestamp="00:00:45")
            
            poster_url = f"/static/thumbnails/{safe_name}_poster.jpg"
            backdrop_url = f"/static/backdrops/{safe_name}_back.jpg"
            
            cur.execute("UPDATE movies SET poster_url = ?, backdrop_url = ? WHERE id = ?", (poster_url, backdrop_url, mid))
            print(f"🚀 Updated DB for {title}")
        else:
            print(f"❌ Could not find local file for {title}")
            
    conn.commit()
    conn.close()

if __name__ == "__main__":
    asyncio.run(recover_thumbnails())
