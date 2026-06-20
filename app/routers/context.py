"""Resolved learning context for the frontend context panel."""
from fastapi import APIRouter, Depends, Request

from app.core.security import User, current_user
from app.schemas.chat import ChatRequest, CurrentContext

router = APIRouter(prefix="/api/v1/tutor", tags=["tutor"])


@router.get("/context", response_model=CurrentContext)
async def get_context(
    request: Request,
    courseId: str = "demo-course",
    lessonId: str | None = None,
    user: User = Depends(current_user),
):
    builder = request.app.state.context
    req = ChatRequest(course_id=courseId, lesson_id=lessonId, message="context")
    return await builder.build(user.id, req)
