"""Short-term conversation memory. Uses Redis when configured, otherwise an
in-process dict so the service runs standalone. Long-term (MySQL) persistence and
summarization are the next increment."""
import json
import logging
from collections import defaultdict

from app.core.config import settings

log = logging.getLogger("memory")


class MemoryService:
    WINDOW = 12      # turns surfaced into the prompt
    KEEP = 50        # turns retained in the store

    def __init__(self) -> None:
        self._redis = None
        self._mem: dict[str, list[dict]] = defaultdict(list)
        if settings.REDIS_URL:
            try:
                import redis.asyncio as redis  # lazy

                self._redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
            except Exception as exc:  # pragma: no cover
                log.warning("redis init failed: %s", exc)

    @property
    def backend(self) -> str:
        return "redis" if self._redis else "in-memory"

    def _key(self, conversation_id: str) -> str:
        return f"tutor:conv:{conversation_id}"

    async def load(self, conversation_id: str | None) -> dict:
        if not conversation_id:
            return {"summary": "", "window": []}
        if self._redis:
            try:
                raw = await self._redis.lrange(self._key(conversation_id), -self.WINDOW, -1)
                return {"summary": "", "window": [json.loads(x) for x in raw]}
            except Exception as exc:
                log.warning("memory load failed: %s", exc)
        return {"summary": "", "window": self._mem[conversation_id][-self.WINDOW:]}

    async def append(self, conversation_id: str, user_msg: str, assistant_msg: str) -> None:
        turns = [
            {"role": "user", "content": user_msg},
            {"role": "assistant", "content": assistant_msg},
        ]
        if self._redis:
            try:
                pipe = self._redis.pipeline()
                for t in turns:
                    pipe.rpush(self._key(conversation_id), json.dumps(t))
                pipe.ltrim(self._key(conversation_id), -self.KEEP, -1)
                await pipe.execute()
                return
            except Exception as exc:
                log.warning("memory append failed: %s", exc)
        self._mem[conversation_id].extend(turns)
        self._mem[conversation_id] = self._mem[conversation_id][-self.KEEP:]
