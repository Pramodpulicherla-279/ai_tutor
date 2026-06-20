"""Assembles the CurrentContext for a turn: lesson framing, skill mode, progress
and weak topics. Falls back to request-supplied fields when the platform/DB are
not wired, so it always returns a usable context."""
import logging

from app.schemas.chat import ChatRequest, CurrentContext
from app.services.platform_client import PlatformClient

log = logging.getLogger("context")

SOCRATIC = {"beginner": 1, "intermediate": 2, "advanced": 3}


class ContextBuilder:
    def __init__(self, platform: PlatformClient) -> None:
        self.platform = platform

    async def build(self, user_id: str, req: ChatRequest) -> CurrentContext:
        lesson_title = req.lesson_title or "this lesson"
        topic = req.topic or ""
        progress_summary = "no progress data yet"

        if req.lesson_id and self.platform.enabled:
            lesson = await self.platform.get_lesson(req.lesson_id)
            if lesson:
                lesson_title = lesson.get("title", lesson_title)
                topic = topic or lesson.get("topic", "")

        # Skill mode resolution (Phase 9) goes here once topic_mastery is wired.
        skill_mode = "beginner"

        scope = {
            "course_id": req.course_id,
            "lesson_ids": [req.lesson_id] if req.lesson_id else None,
        }
        return CurrentContext(
            user_id=user_id,
            course_id=req.course_id,
            module_id=req.module_id,
            lesson_id=req.lesson_id,
            lesson_title=lesson_title,
            topic=topic,
            skill_mode=skill_mode,
            socratic_level=SOCRATIC[skill_mode],
            progress_summary=progress_summary,
            weak_topics=[],
            scope=scope,
        )
