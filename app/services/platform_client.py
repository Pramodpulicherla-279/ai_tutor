"""Thin read-only client for the existing Node/Express platform (source of truth
for courses, lessons and progress). Cache-aside belongs here; for now it is a
direct fetch with a short timeout and graceful failure."""
import logging

from app.core.config import settings

log = logging.getLogger("platform")


class PlatformClient:
    def __init__(self) -> None:
        self._http = None
        if settings.PLATFORM_API_URL:
            try:
                import httpx  # lazy

                self._http = httpx.AsyncClient(
                    base_url=settings.PLATFORM_API_URL, timeout=4.0
                )
            except Exception as exc:  # pragma: no cover
                log.warning("platform client init failed: %s", exc)

    @property
    def enabled(self) -> bool:
        return self._http is not None

    async def get_lesson(self, lesson_id: str) -> dict | None:
        if not self._http:
            return None
        try:
            r = await self._http.get(f"/api/lessons/{lesson_id}")
            if r.status_code == 200:
                return r.json()
        except Exception as exc:
            log.warning("get_lesson failed: %s", exc)
        return None

    async def get_progress(self, user_id: str, course_id: str) -> dict | None:
        if not self._http:
            return None
        try:
            r = await self._http.get(
                f"/api/users/{user_id}/progress", params={"courseId": course_id}
            )
            if r.status_code == 200:
                return r.json()
        except Exception as exc:
            log.warning("get_progress failed: %s", exc)
        return None

    async def aclose(self) -> None:
        if self._http:
            await self._http.aclose()
