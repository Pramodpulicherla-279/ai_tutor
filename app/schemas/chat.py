"""Request / response / streaming-event models for the tutor API."""
from typing import Literal, Optional

from pydantic import BaseModel, Field

Mode = Literal["tutor", "coding", "quiz", "revision", "summary"]


class ChatRequest(BaseModel):
    conversation_id: Optional[str] = None
    course_id: str = "demo-course"
    module_id: Optional[str] = None
    lesson_id: Optional[str] = None
    lesson_title: Optional[str] = None
    lesson_slug: Optional[str] = None
    topic: Optional[str] = None
    mode: Mode = "tutor"
    message: str = Field(min_length=1, max_length=4000)


class Citation(BaseModel):
    chroma_id: str
    lesson_id: str = ""
    lesson_slug: str = ""
    score: float = 0.0


class ChatEvent(BaseModel):
    """One server-sent event. Serialized as `data: {json}\\n\\n`."""
    type: Literal["start", "citations", "token", "done", "error"]
    delta: Optional[str] = None
    citations: Optional[list[Citation]] = None
    conversation_id: Optional[str] = None
    message_id: Optional[str] = None
    usage: Optional[dict] = None
    detail: Optional[str] = None


class CurrentContext(BaseModel):
    user_id: str
    course_id: str
    module_id: Optional[str] = None
    lesson_id: Optional[str] = None
    lesson_title: str = "this lesson"
    topic: str = ""
    skill_mode: str = "beginner"
    socratic_level: int = 2
    progress_summary: str = "no progress data yet"
    weak_topics: list[str] = Field(default_factory=list)
    scope: dict = Field(default_factory=dict)
