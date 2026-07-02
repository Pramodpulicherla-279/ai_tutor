"""Request / response / streaming-event models for the tutor API."""
from typing import Literal, Optional

from pydantic import BaseModel, Field

# "sandbox" = the in-editor Code Guide: strictly scoped to the learner's code.
Mode = Literal["tutor", "coding", "quiz", "revision", "summary", "sandbox", "code_review"]


class ChatRequest(BaseModel):
    conversation_id: Optional[str] = None
    course_id: str = "demo-course"
    module_id: Optional[str] = None
    lesson_id: Optional[str] = None
    lesson_title: Optional[str] = None
    lesson_slug: Optional[str] = None
    topic: Optional[str] = None
    learner_name: Optional[str] = None
    mode: Mode = "tutor"
    # Code Guide bundles the editor files into the message, so allow more room
    # than a plain chat line while still capping the payload.
    message: str = Field(min_length=1, max_length=8000)


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
    learner_name: str = "there"
    skill_mode: str = "beginner"
    socratic_level: int = 2
    progress_summary: str = "no progress data yet"
    weak_topics: list[str] = Field(default_factory=list)
    scope: dict = Field(default_factory=dict)
