"""Generation via Google Gemini 2.5 Flash. Streams tokens. Without GEMINI_API_KEY it
runs a deterministic mock streamer so the whole service is demoable with zero creds.

Gemini specifics: the system prompt goes to `system_instruction`; chat turns become
`contents` with roles user/model (assistant -> model)."""
import asyncio
import logging

from app.core.config import settings

log = logging.getLogger("llm")


class LLMClient:
    def __init__(self) -> None:
        self._client = None
        self.last_usage: dict = {}
        if settings.GEMINI_API_KEY:
            try:
                from google import genai  # lazy: only needed when configured

                self._client = genai.Client(api_key=settings.GEMINI_API_KEY)
            except Exception as exc:  # pragma: no cover
                log.warning("gemini init failed: %s", exc)

    @property
    def live(self) -> bool:
        return self._client is not None

    def _model_for(self, mode: str, skill: str) -> str:
        if mode in ("quiz", "summary"):
            return settings.MODEL_FAST
        return settings.MODEL_SMART

    @staticmethod
    def _to_contents(messages: list[dict]) -> list[dict]:
        contents = []
        for m in messages:
            role = "model" if m.get("role") == "assistant" else "user"
            contents.append({"role": role, "parts": [{"text": m.get("content", "")}]})
        return contents

    async def stream(self, system_text: str, messages: list[dict], mode: str = "tutor",
                     skill: str = "beginner"):
        if not self._client:
            async for delta in self._mock_stream(messages):
                yield delta
            return

        from google.genai import types  # lazy

        model = self._model_for(mode, skill)
        config = types.GenerateContentConfig(
            system_instruction=system_text,
            max_output_tokens=settings.MAX_OUTPUT_TOKENS,
            temperature=settings.TEMPERATURE,
        )
        try:
            stream = await self._client.aio.models.generate_content_stream(
                model=model, contents=self._to_contents(messages), config=config
            )
            usage = None
            async for chunk in stream:
                if getattr(chunk, "usage_metadata", None):
                    usage = chunk.usage_metadata
                if getattr(chunk, "text", None):
                    yield chunk.text
            self.last_usage = {
                "model": model,
                "input_tokens": getattr(usage, "prompt_token_count", None),
                "output_tokens": getattr(usage, "candidates_token_count", None),
            }
        except Exception as exc:
            log.error("llm stream failed: %s", exc)
            self.last_usage = {"model": model, "error": str(exc)}
            yield f"\n\n_(The model call failed: {exc})_"

    async def _mock_stream(self, messages: list[dict]):
        user = messages[-1]["content"] if messages else ""
        user = user.replace("<student_message>", "").replace("</student_message>", "")
        reply = (
            "Great question — let's reason through it together. "
            f"You're asking about: \"{user[:140].strip()}\". "
            "Before I explain, what do you already know about it? "
            "Here's a nudge: think about the smallest example that would show the idea, "
            "then tell me what you expect to happen. "
            "_(mock tutor — set GEMINI_API_KEY for real answers.)_"
        )
        words = reply.split(" ")
        self.last_usage = {"model": "mock", "input_tokens": 0, "output_tokens": len(words)}
        for word in words:
            yield word + " "
            await asyncio.sleep(0.02)
