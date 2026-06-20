"""MongoDB collection names + index definitions for the `ai_tutor` database, mirroring
docs/dev-el-ai-tutor/02-data-layer.md (now on MongoDB instead of MySQL).

Document shapes (informal):
  conversations:  {_id: str(uuid), user_id, course_id, module_id, lesson_id, mode,
                   title, summary, status, message_count, last_message_at, created_at}
  messages:       {_id, conversation_id, role, content, intent, model, tokens_in,
                   tokens_out, citations, created_at}
  knowledge_gaps: {_id, user_id, course_id, topic, gap_score, evidence_count, status,
                   last_seen_at}
  topic_mastery:  {_id, user_id, course_id, topic, mastery, attempts, correct, updated_at}
  question_events:{_id, user_id, course_id, lesson_id, topic, intent, resolved, created_at}
  revision_items: {_id, user_id, course_id, topic, ease, interval_d, reps, due_at}
  suggested_questions: {_id, lesson_id, text, intent, ord}
  content_chunks: {_id, text, course_id, course_slug, module_id, lesson_id, lesson_slug,
                   topic, level, source_type, chunk_index, version, token_count, language}
                  -> Atlas Vector Search auto-embeds `text` (see VECTOR_INDEX).
"""
COLLECTIONS = [
    "tutor_users",
    "conversations",
    "messages",
    "knowledge_gaps",
    "topic_mastery",
    "question_events",
    "revision_items",
    "suggested_questions",
    "content_chunks",
]

# (keys, options) per collection. Explicit names keep these consistent with any
# indexes pre-created out-of-band (MCP/Atlas UI). Unique where it protects an invariant.
INDEXES: dict[str, list[tuple[list[tuple[str, int]], dict]]] = {
    "conversations": [
        ([("user_id", 1), ("last_message_at", -1)], {"name": "conv_user_recent"}),
        ([("user_id", 1), ("lesson_id", 1)], {"name": "conv_user_lesson"}),
    ],
    "messages": [
        ([("conversation_id", 1), ("created_at", 1)], {"name": "msg_conv"}),
    ],
    "knowledge_gaps": [
        ([("user_id", 1), ("course_id", 1), ("topic", 1)],
         {"name": "gap_unique", "unique": True}),
        ([("user_id", 1), ("status", 1)], {"name": "gap_user_status"}),
    ],
    "topic_mastery": [
        ([("user_id", 1), ("course_id", 1), ("topic", 1)],
         {"name": "mastery_unique", "unique": True}),
    ],
    "question_events": [
        ([("user_id", 1), ("course_id", 1), ("created_at", 1)], {"name": "qe_user_course"}),
    ],
    "revision_items": [
        ([("user_id", 1), ("due_at", 1)], {"name": "rev_due"}),
    ],
    "suggested_questions": [
        ([("lesson_id", 1), ("ord", 1)], {"name": "sq_lesson"}),
    ],
}


async def ensure_indexes(db) -> None:
    """Idempotently create the classic indexes. Safe to call on every startup.
    The Atlas Vector Search index on content_chunks is created out-of-band (MCP/Atlas)."""
    if db is None:
        return
    for coll, specs in INDEXES.items():
        for keys, opts in specs:
            await db[coll].create_index(keys, **opts)
