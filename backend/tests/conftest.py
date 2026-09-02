import pytest
import pytest_asyncio
from app.db.database import init_db

@pytest_asyncio.fixture(autouse=True, scope="function")
async def setup_test_db():
    """Ensure database tables and WAL mode are initialized before each test."""
    await init_db()
