import asyncio
import sqlite3
import os
from backend.core.config import get_settings

async def migrate():
    settings = get_settings()
    # Extract path from sqlite+aiosqlite:///d:\CinemaProject\TelegramFilm\backend\cinema.db
    db_path = settings.DATABASE_URL.split("///")[-1]
    print(f"Migrating database at: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Add size_bytes column
        cursor.execute("ALTER TABLE movies ADD COLUMN size_bytes INTEGER")
        print("Added size_bytes column")
    except sqlite3.OperationalError:
        print("size_bytes column already exists")

    try:
        # Add created_at column
        cursor.execute("ALTER TABLE movies ADD COLUMN created_at TEXT")
        print("Added created_at column")
    except sqlite3.OperationalError:
        print("created_at column already exists")

    conn.commit()
    conn.close()
    print("Migration complete!")

if __name__ == "__main__":
    asyncio.run(migrate())
