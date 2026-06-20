"""Conversation history for the frontend (list + replay). Returns [] when MongoDB is
not configured."""
from fastapi import APIRouter, Depends, Request

from app.core.security import User, current_user

router = APIRouter(prefix="/api/v1/tutor", tags=["tutor"])


@router.get("/conversations")
async def list_conversations(request: Request, user: User = Depends(current_user)):
    return {"items": await request.app.state.repo.list_conversations(user.id)}


@router.get("/conversations/{conversation_id}/messages")
async def get_messages(
    conversation_id: str, request: Request, user: User = Depends(current_user)
):
    return {"items": await request.app.state.repo.get_messages(conversation_id)}
