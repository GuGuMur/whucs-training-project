"""MinIO/S3 object storage adapter for file backup (FR-F10)."""
from __future__ import annotations
import logging, io
from minio import Minio
from minio.error import S3Error
from app.core.config import settings

logger = logging.getLogger(__name__)

_client: Minio | None = None

def _get_client() -> Minio | None:
    global _client
    if _client is not None:
        return _client
    try:
        _client = Minio(
            settings.S3_ENDPOINT,
            access_key=settings.S3_ACCESS_KEY,
            secret_key=settings.S3_SECRET_KEY,
            secure=settings.S3_SECURE,
        )
        if not _client.bucket_exists(settings.S3_BUCKET):
            _client.make_bucket(settings.S3_BUCKET)
        logger.info("S3 connected: %s/%s", settings.S3_ENDPOINT, settings.S3_BUCKET)
        return _client
    except Exception as e:
        logger.warning("S3 unavailable, using local storage: %s", e)
        _client = None
        return None

async def backup_file(file_id: str, filename: str, content: bytes) -> str:
    """Store file in S3. Returns storage key or raises."""
    client = _get_client()
    if client is None:
        raise RuntimeError("S3 not available")
    key = f"files/{file_id}/{filename}"
    client.put_object(settings.S3_BUCKET, key, io.BytesIO(content), len(content))
    return key

async def get_file(key: str) -> bytes:
    client = _get_client()
    if client is None:
        raise RuntimeError("S3 not available")
    resp = client.get_object(settings.S3_BUCKET, key)
    return resp.read()

def s3_available() -> bool:
    return _get_client() is not None
