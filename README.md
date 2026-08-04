# dev.el AI Tutor — service

Context-aware AI Tutor microservice (FastAPI). Boots and streams answers **with zero
infrastructure** (mock tutor, in-memory memory), then upgrades to **Gemini 2.5 Flash**
generation, **MongoDB `ai_tutor`** persistence and **Atlas Vector Search** retrieval as
you set env vars.

Design docs: [`../docs/dev-el-ai-tutor/`](../docs/dev-el-ai-tutor/README.md).

## Stack
| Concern | Tech |
|---|---|
| Generation | Google **Gemini 3.6 Flash** (`google-genai`) |
| Tutor data (conversations, messages, analytics, gaps) | **MongoDB** `ai_tutor` (motor) |
| Lesson-content retrieval (RAG) | **MongoDB Atlas Vector Search** (auto-embedding) |
| Short-term memory / cache | Redis (optional; in-memory fallback) |
| Identity | JWT shared with the Node platform |

## Quick start (mock mode, no keys)
```bash
cd ai-tutor
python -m venv .venv && .venv\Scripts\activate      # Windows
pip install -e ".[dev]"
uvicorn app.main:app --reload
```
```bash
curl http://localhost:8000/ready
curl -N -X POST http://localhost:8000/api/v1/tutor/chat \
  -H "Content-Type: application/json" \
  -d '{"course_id":"python","lesson_title":"Variables","message":"What is a variable?","mode":"tutor"}'
```
Interactive docs at http://localhost:8000/docs.

## Go live
```bash
pip install -e ".[integrations]"
cp .env.example .env        # set GEMINI_API_KEY and MONGODB_URI
```
`/ready` reports each integration as live vs degraded. On startup the app idempotently
creates the classic indexes in `ai_tutor`.

> **Vector search needs MongoDB Atlas.** The `$vectorSearch` retrieval path requires an
> Atlas cluster (or an `atlas-local` dev deployment) — a community/standalone MongoDB
> cannot host the auto-embedding index. Until `MONGODB_URI` points at Atlas with the
> `content_vindex` index present, retrieval **degrades gracefully** (the tutor answers
> from general knowledge and says so). The relational collections work on any MongoDB.

## Endpoints
| Method | Path | Notes |
|---|---|---|
| GET | `/health`, `/ready` | liveness / integration status |
| POST | `/api/v1/tutor/chat` | SSE stream (`data: {json}\n\n`) |
| POST | `/api/v1/tutor/chat/sync` | full answer JSON |
| GET | `/api/v1/tutor/context` | resolved learning context |
| GET | `/api/v1/tutor/conversations` | list user's conversations |
| GET | `/api/v1/tutor/conversations/{id}/messages` | replay a conversation |
| GET | `/api/v1/tutor/suggestions` | suggested-question chips |

## Layout
```
app/
  core/          config, logging, JWT security
  schemas/       pydantic request/response/event models
  services/      context · retrieval (Atlas) · memory · prompt · llm (Gemini) · orchestrator · platform
  repositories/  MongoDB persistence (conversations, messages)
  routers/       chat · conversations · context · suggestions · health
  db/            motor client (session) + collections/indexes (models)
tests/           smoke tests (mock mode)
```

## What's real vs next
**Working now:** streaming chat (mock + live Gemini), Socratic mode-aware prompts,
MongoDB persistence (graceful when offline), conversation history, JWT, smoke tests.
The `ai_tutor` database + collections + query indexes are provisioned.

**Next:** point `MONGODB_URI` at Atlas + create the `content_vindex` vector index, build
the ingestion worker (lesson → chunk → `content_chunks` for auto-embedding), and add the
AnalyticsService / RecommendationEngine / `/quiz/generate`.

## Test
```bash
pytest
```
