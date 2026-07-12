"""Ensure database tables exist before any test runs."""

import asyncio

import pytest


@pytest.fixture(scope="session", autouse=True)
def _ensure_db_tables():
    """Create all database tables once at the start of the test session."""
    from app.core.database import engine, Base

    async def _create():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        asyncio.run(_create())
    else:
        import concurrent.futures

        future = asyncio.run_coroutine_threadsafe(_create(), loop)
        future.result(timeout=30)
