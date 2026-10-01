from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .config import get_settings
from .models import Base

settings = get_settings()
is_sqlite = settings.DATABASE_URL.startswith("sqlite")

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False, "timeout": 30} if is_sqlite else {},
)


if is_sqlite:
    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA busy_timeout=30000")
        cursor.close()


AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        if is_sqlite:
            # Existing installations predate the model-level unique constraint.
            # Keep the newest row per user/movie before adding the runtime index.
            await conn.exec_driver_sql(
                """
                DELETE FROM watch_history
                WHERE id NOT IN (
                    SELECT MAX(id)
                    FROM watch_history
                    GROUP BY user_telegram_id, movie_id
                )
                """
            )
            await conn.exec_driver_sql(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS uq_watch_history_user_movie
                ON watch_history(user_telegram_id, movie_id)
                """
            )


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
