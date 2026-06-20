"""Async MongoDB connection (motor). Returns None when MONGODB_URI is unset so the
service runs standalone (no persistence, no retrieval). The `ai_tutor` database lives
on the same cluster as the platform's `devora` database."""
import logging

from app.core.config import settings

log = logging.getLogger("mongo")

_client = None
_db = None


def init_db() -> None:
    global _client, _db
    if not settings.MONGODB_URI:
        log.warning("MONGODB_URI not set — persistence and retrieval are disabled")
        return
    try:
        from motor.motor_asyncio import AsyncIOMotorClient  # lazy

        _client = AsyncIOMotorClient(settings.MONGODB_URI, uuidRepresentation="standard")
        _db = _client[settings.MONGO_DB]
        log.info("connected to MongoDB database=%s", settings.MONGO_DB)
    except Exception as exc:  # pragma: no cover
        log.warning("mongo init failed: %s", exc)


def get_db():
    """Return the motor database handle, or None when MongoDB is not configured."""
    return _db


async def close_db() -> None:
    if _client is not None:
        _client.close()
