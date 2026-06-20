"""Durable conversation/message persistence in MongoDB. All methods no-op gracefully
when MongoDB is not configured (get_db() returns None), so the chat path always works."""
import logging
import uuid
from datetime import datetime, timezone

log = logging.getLogger("repo")


def _now() -> datetime:
    return datetime.now(timezone.utc)


class ConversationRepo:
    def __init__(self, get_db) -> None:
        self._get_db = get_db

    async def persist_turn(self, conv_id, user_id, req, user_msg, assistant_msg,
                           usage, citations):
        db = self._get_db()
        if db is None:
            return None
        try:
            now = _now()
            await db.conversations.update_one(
                {"_id": conv_id},
                {
                    "$setOnInsert": {
                        "_id": conv_id,
                        "user_id": user_id,
                        "course_id": req.course_id,
                        "module_id": req.module_id,
                        "lesson_id": req.lesson_id,
                        "mode": req.mode,
                        "status": "active",
                        "created_at": now,
                    },
                    "$set": {"last_message_at": now},
                    "$inc": {"message_count": 2},
                },
                upsert=True,
            )
            await db.messages.insert_many([
                {
                    "_id": str(uuid.uuid4()),
                    "conversation_id": conv_id,
                    "role": "user",
                    "content": user_msg,
                    "intent": req.mode,
                    "created_at": now,
                },
                {
                    "_id": str(uuid.uuid4()),
                    "conversation_id": conv_id,
                    "role": "assistant",
                    "content": assistant_msg,
                    "model": (usage or {}).get("model"),
                    "tokens_in": (usage or {}).get("input_tokens"),
                    "tokens_out": (usage or {}).get("output_tokens"),
                    "citations": citations,
                    "created_at": now,
                },
            ])
            return conv_id
        except Exception as exc:  # pragma: no cover
            log.warning("persist_turn failed: %s", exc)
            return None

    async def list_conversations(self, user_id: str, limit: int = 20):
        db = self._get_db()
        if db is None:
            return []
        cur = db.conversations.find(
            {"user_id": user_id}, {"summary": 0}
        ).sort("last_message_at", -1).limit(limit)
        return [doc async for doc in cur]

    async def get_messages(self, conversation_id: str, limit: int = 200):
        db = self._get_db()
        if db is None:
            return []
        cur = db.messages.find(
            {"conversation_id": conversation_id}
        ).sort("created_at", 1).limit(limit)
        return [doc async for doc in cur]
