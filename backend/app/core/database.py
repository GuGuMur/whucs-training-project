from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

_db_url = settings.DATABASE_URL
if _db_url.startswith("sqlite:///"):
    _db_url = _db_url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)

engine = create_async_engine(_db_url, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(_ensure_sqlite_schema)


def _ensure_sqlite_schema(conn) -> None:
    if not str(engine.url).startswith("sqlite"):
        return

    kb_columns = {row[1] for row in conn.exec_driver_sql("PRAGMA table_info(knowledge_bases)").fetchall()}
    kb_additions = {
        "scope_type": "ALTER TABLE knowledge_bases ADD COLUMN scope_type VARCHAR(16) DEFAULT 'personal' NOT NULL",
        "scope_id": "ALTER TABLE knowledge_bases ADD COLUMN scope_id VARCHAR(64)",
        "category": "ALTER TABLE knowledge_bases ADD COLUMN category VARCHAR(80) DEFAULT '' NOT NULL",
        "tags": "ALTER TABLE knowledge_bases ADD COLUMN tags TEXT DEFAULT '[]' NOT NULL",
        "freshness_policy": "ALTER TABLE knowledge_bases ADD COLUMN freshness_policy VARCHAR(32) DEFAULT 'manual' NOT NULL",
        "last_indexed_at": "ALTER TABLE knowledge_bases ADD COLUMN last_indexed_at DATETIME",
    }
    for column, statement in kb_additions.items():
        if column not in kb_columns:
            conn.exec_driver_sql(statement)

    doc_columns = {row[1] for row in conn.exec_driver_sql("PRAGMA table_info(knowledge_documents)").fetchall()}
    doc_additions = {
        "version_sha": "ALTER TABLE knowledge_documents ADD COLUMN version_sha VARCHAR(64) DEFAULT '' NOT NULL",
        "error_message": "ALTER TABLE knowledge_documents ADD COLUMN error_message TEXT DEFAULT '' NOT NULL",
        "content_text": "ALTER TABLE knowledge_documents ADD COLUMN content_text TEXT DEFAULT '' NOT NULL",
        "summary": "ALTER TABLE knowledge_documents ADD COLUMN summary TEXT DEFAULT '' NOT NULL",
        "keywords": "ALTER TABLE knowledge_documents ADD COLUMN keywords TEXT DEFAULT '[]' NOT NULL",
        "outline": "ALTER TABLE knowledge_documents ADD COLUMN outline TEXT DEFAULT '[]' NOT NULL",
        "char_count": "ALTER TABLE knowledge_documents ADD COLUMN char_count INTEGER DEFAULT 0 NOT NULL",
        "token_count": "ALTER TABLE knowledge_documents ADD COLUMN token_count INTEGER DEFAULT 0 NOT NULL",
    }
    for column, statement in doc_additions.items():
        if column not in doc_columns:
            conn.exec_driver_sql(statement)
