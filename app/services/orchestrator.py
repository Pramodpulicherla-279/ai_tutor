"""Ties the services together for a single tutor turn and yields ChatEvents.
Context-build and memory-load run concurrently to cut time-to-first-token. Retrieval
uses Atlas Vector Search directly on the query text. Persistence (Mongo) and short-term
memory updates run after the stream and never block the answer."""
import asyncio
import logging
import uuid

from app.schemas.chat import ChatEvent, ChatRequest, CurrentContext

log = logging.getLogger("orchestrator")


class TutorOrchestrator:
    def __init__(self, ctx, memory, retrieval, prompt, llm, repo):
        self.ctx = ctx
        self.memory = memory
        self.retrieval = retrieval
        self.prompt = prompt
        self.llm = llm
        self.repo = repo

    async def run(self, user_id: str, req: ChatRequest):
        conv_id = req.conversation_id or str(uuid.uuid4())
        yield ChatEvent(type="start", conversation_id=conv_id)

        context, memory = await asyncio.gather(
            self.ctx.build(user_id, req),
            self.memory.load(req.conversation_id),
            return_exceptions=True,
        )
        if isinstance(context, BaseException):
            log.warning("context build failed: %s", context)
            context = CurrentContext(user_id=user_id, course_id=req.course_id,
                                     lesson_id=req.lesson_id,
                                     scope={"course_id": req.course_id})
        if isinstance(memory, BaseException):
            memory = {"summary": "", "window": []}

        chunks = await self.retrieval.retrieve(req.message, context.scope, req.mode)
        citations = [c.citation() for c in chunks]
        if citations:
            yield ChatEvent(type="citations", citations=citations)

        system_text, messages = self.prompt.build(
            context, chunks, memory, req.message, req.mode
        )

        acc: list[str] = []
        async for delta in self.llm.stream(
            system_text, messages, mode=req.mode, skill=context.skill_mode
        ):
            acc.append(delta)
            yield ChatEvent(type="token", delta=delta)

        answer = "".join(acc)
        # Side effects: short-term window (Redis) + durable persistence (Mongo).
        try:
            await self.memory.append(conv_id, req.message, answer)
        except Exception as exc:  # pragma: no cover
            log.warning("memory append failed: %s", exc)
        message_id = await self.repo.persist_turn(
            conv_id, user_id, req, req.message, answer,
            usage=self.llm.last_usage,
            citations=[c.model_dump() for c in citations],
        )

        yield ChatEvent(
            type="done",
            conversation_id=conv_id,
            message_id=str(message_id or uuid.uuid4()),
            usage=self.llm.last_usage,
        )
