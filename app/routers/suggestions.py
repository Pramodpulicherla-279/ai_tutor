"""Suggested-question chips. Static defaults for now; back this with the
suggested_questions table / RecommendationEngine next."""
from fastapi import APIRouter, Depends

from app.core.security import User, current_user

router = APIRouter(prefix="/api/v1/tutor", tags=["tutor"])

_DEFAULTS = [
    {"text": "Explain this concept simply", "intent": "tutor"},
    {"text": "Show me a code example", "intent": "coding"},
    {"text": "Quiz me on this lesson", "intent": "quiz"},
    {"text": "Summarize this lesson", "intent": "summary"},
]


@router.get("/suggestions")
async def suggestions(lessonId: str | None = None, user: User = Depends(current_user)):
    return {"lesson_id": lessonId, "items": _DEFAULTS}
