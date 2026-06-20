"""Liveness and readiness. /ready reports which integrations are live vs degraded."""
from fastapi import APIRouter, Request

from app.db.session import get_db

router = APIRouter(tags=["meta"])


@router.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@router.get("/ready")
async def ready(request: Request) -> dict:
    s = request.app.state
    return {
        "status": "ready",
        "llm": "live" if s.llm.live else "mock",
        "database": "connected" if get_db() is not None else "disconnected",
        "retrieval": s.retrieval.enabled,
        "memory": s.memory.backend,
        "platform": s.platform.enabled,
    }
