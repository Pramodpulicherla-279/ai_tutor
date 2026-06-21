"""Lesson-content retrieval via MongoDB Atlas Vector Search ($vectorSearch).

The `content_chunks` collection is indexed with an auto-embedding vector index, so we
pass the learner's question as text and Atlas embeds + searches it — no separate
embedding call in the app. Returns [] (ungrounded answer) when Mongo/the index are
absent, so the tutor still responds."""
import logging

from app.core.config import settings
from app.schemas.chat import Citation

log = logging.getLogger("retrieval")


class Chunk:
    def __init__(self, text: str, metadata: dict | None, score: float) -> None:
        self.text = text
        self.metadata = metadata or {}
        self.score = score

    def citation(self) -> Citation:
        m = self.metadata
        return Citation(
            chroma_id=str(m.get("_id", "")),
            lesson_id=str(m.get("lesson_id", "")),
            lesson_slug=str(m.get("lesson_slug", "")),
            score=float(self.score or 0.0),
        )


class RetrievalService:
    def __init__(self, get_db) -> None:
        self._get_db = get_db

    @property
    def enabled(self) -> bool:
        return self._get_db() is not None

    def _filter(self, scope: dict, intent: str) -> dict:
        clause: dict = {}
        if scope.get("course_id"):
            clause["course_id"] = scope["course_id"]
        lesson_ids = scope.get("lesson_ids")
        if lesson_ids:
            clause["lesson_id"] = {"$in": lesson_ids}
        if intent in ("coding", "sandbox"):
            clause["source_type"] = "code_example"
        return clause

    async def retrieve(self, query_text: str, scope: dict, intent: str, k: int | None = None):
        db = self._get_db()
        if db is None or not query_text:
            return []
        k = k or settings.RETRIEVAL_K
        vsearch: dict = {
            "index": settings.VECTOR_INDEX,
            "path": "text",          # auto-embedded source field
            "query": query_text,     # Atlas embeds the query text automatically
            "numCandidates": k * 10,
            "limit": k,
        }
        flt = self._filter(scope, intent)
        if flt:
            vsearch["filter"] = flt
        pipeline = [
            {"$vectorSearch": vsearch},
            {"$project": {
                "text": 1, "lesson_id": 1, "lesson_slug": 1, "course_id": 1,
                "source_type": 1, "score": {"$meta": "vectorSearchScore"},
            }},
        ]
        try:
            cursor = db[settings.VECTOR_COLLECTION].aggregate(pipeline)
            return [
                Chunk(doc.get("text", ""), doc, doc.get("score", 0.0))
                async for doc in cursor
            ]
        except Exception as exc:
            log.warning("vector search failed (index may not be ready): %s", exc)
            return []
