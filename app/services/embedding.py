"""Embeddings are now generated and managed by MongoDB Atlas Vector Search
(auto-embedding index on `content_chunks.text`). The application no longer calls an
embedding API directly — retrieval passes the query as text and Atlas embeds it.

This module is intentionally left as a stub; see services/retrieval.py.
"""
