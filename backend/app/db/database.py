import os
import shutil
import logging
from datetime import datetime
from pathlib import Path
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base

from app.config import settings

logger = logging.getLogger("ogcai.database")

# Ensure db directory exists
settings.DB_DIR.mkdir(parents=True, exist_ok=True)
BACKUP_DIR = settings.DB_DIR / "backups"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

DB_FILE_PATH = settings.DB_DIR / "ogcai.db"
# Use aiosqlite as async SQLite driver
DATABASE_URL = f"sqlite+aiosqlite:///{DB_FILE_PATH.as_posix()}"

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False
)

Base = declarative_base()

async def init_db():
    """Initialize database schemas and enforce SQLite WAL Mode."""
    async with engine.begin() as conn:
        # Enable WAL mode for high concurrency
        await conn.execute(Base.metadata.schema_literal("PRAGMA journal_mode=WAL;")) if hasattr(Base.metadata, "schema_literal") else None
        # Raw execution of PRAGMAs
        from sqlalchemy import text
        await conn.execute(text("PRAGMA journal_mode=WAL;"))
        await conn.execute(text("PRAGMA synchronous=NORMAL;"))
        await conn.execute(text("PRAGMA foreign_keys=ON;"))
        
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
    logger.info(f"Database initialized in WAL Mode at {DB_FILE_PATH}")

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI Dependency for database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

def backup_database(max_backups: int = 10) -> str:
    """Create a point-in-time backup snapshot of ogcai.db into backups/ folder."""
    if not DB_FILE_PATH.exists():
        return ""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = BACKUP_DIR / f"ogcai_backup_{timestamp}.db"
    
    try:
        shutil.copy2(DB_FILE_PATH, backup_file)
        logger.info(f"Database snapshot created: {backup_file}")
        
        # Clean up old backups exceeding max_backups
        backups = sorted(BACKUP_DIR.glob("ogcai_backup_*.db"), key=os.path.getmtime)
        if len(backups) > max_backups:
            for old_backup in backups[:-max_backups]:
                old_backup.unlink()
                logger.info(f"Removed old backup: {old_backup}")
                
        return str(backup_file)
    except Exception as e:
        logger.error(f"Failed to create database backup: {e}")
        return ""
