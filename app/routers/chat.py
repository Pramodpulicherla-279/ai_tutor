"""Chat endpoints. /chat streams Server-Sent Events as `data: {json}\\n\\n` frames,
matching the frontend's fetch-stream parser. /chat/sync returns the full answer."""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from app.core.security import User, current_user
from app.schemas.chat import ChatRequest

router = APIRouter(prefix="/api/v1/tutor", tags=["tutor"])

_SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",  # disable proxy buffering so tokens flush immediately
}


@router.post("/chat")
async def chat(req: ChatRequest, request: Request, user: User = Depends(current_user)):
    orch = request.app.state.orchestrator

    async def gen():
        async for event in orch.run(user.id, req):
            yield f"data: {event.model_dump_json()}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream", headers=_SSE_HEADERS)


@router.post("/chat/sync")
async def chat_sync(req: ChatRequest, request: Request, user: User = Depends(current_user)):
    orch = request.app.state.orchestrator
    text: list[str] = []
    meta: dict = {}
    citations = []
    async for event in orch.run(user.id, req):
        if event.type == "token":
            text.append(event.delta or "")
        elif event.type == "citations":
            citations = event.citations or []
        elif event.type == "done":
            meta = {
                "conversation_id": event.conversation_id,
                "message_id": event.message_id,
                "usage": event.usage,
            }
    return {"answer": "".join(text), "citations": citations, **meta}
