"""App factory + lifespan. Builds service singletons once on startup, connects to
MongoDB (best-effort), ensures indexes, and wires everything onto app.state."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import configure_logging
from app.db.models import ensure_indexes
from app.db.session import close_db, get_db, init_db
from app.repositories.conversations import ConversationRepo
from app.routers import chat, context, conversations, health, suggestions
from app.services.context_builder import ContextBuilder
from app.services.llm_client import LLMClient
from app.services.memory import MemoryService
from app.services.orchestrator import TutorOrchestrator
from app.services.platform_client import PlatformClient
from app.services.prompt_builder import PromptBuilder
from app.services.retrieval import RetrievalService

log = logging.getLogger("startup")


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(settings.LOG_LEVEL)
    init_db()
    try:
        await ensure_indexes(get_db())
    except Exception as exc:  # pragma: no cover - index creation is best-effort
        log.warning("ensure_indexes skipped: %s", exc)

    app.state.platform = PlatformClient()
    app.state.llm = LLMClient()
    app.state.retrieval = RetrievalService(get_db)
    app.state.memory = MemoryService()
    app.state.context = ContextBuilder(app.state.platform)
    app.state.prompt = PromptBuilder()
    app.state.repo = ConversationRepo(get_db)
    app.state.orchestrator = TutorOrchestrator(
        app.state.context,
        app.state.memory,
        app.state.retrieval,
        app.state.prompt,
        app.state.llm,
        app.state.repo,
    )
    try:
        yield
    finally:
        await app.state.platform.aclose()
        await close_db()


def create_app() -> FastAPI:
    app = FastAPI(title=settings.APP_NAME, version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    app.include_router(chat.router)
    app.include_router(context.router)
    app.include_router(conversations.router)
    app.include_router(suggestions.router)
    return app


app = create_app()
