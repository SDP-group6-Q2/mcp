"""Embedding and reranking with fastembed (ONNX: no torch). Models load lazily, once per process.

fastembed is synchronous and CPU-bound, so the async wrappers run it in a worker thread.
"""

import asyncio
import threading
from functools import lru_cache

from app.config import settings

EMBEDDING_DIM = 384  # BAAI/bge-small-en-v1.5; must match VECTOR(384) in schema.sql
_load_lock = threading.Lock()


@lru_cache(maxsize=1)
def _embedder():
    from fastembed import TextEmbedding

    return TextEmbedding(model_name=settings.embedding_model, cache_dir=settings.model_cache_dir)


@lru_cache(maxsize=1)
def _reranker():
    from fastembed.rerank.cross_encoder import TextCrossEncoder

    return TextCrossEncoder(model_name=settings.reranker_model, cache_dir=settings.model_cache_dir)


def _embed_passages(texts: list[str]) -> list[list[float]]:
    with _load_lock:
        model = _embedder()
    return [vector.tolist() for vector in model.passage_embed(texts)]


def _embed_query(text: str) -> list[float]:
    with _load_lock:
        model = _embedder()
    return next(iter(model.query_embed(text))).tolist()


def _rerank(query: str, documents: list[str]) -> list[float]:
    with _load_lock:
        model = _reranker()
    return [float(score) for score in model.rerank(query, documents)]


async def embed_passages(texts: list[str]) -> list[list[float]]:
    return await asyncio.to_thread(_embed_passages, texts)


async def embed_query(text: str) -> list[float]:
    return await asyncio.to_thread(_embed_query, text)


async def rerank(query: str, documents: list[str]) -> list[float]:
    """Relevance score per document (higher is better), in input order."""
    return await asyncio.to_thread(_rerank, query, documents)
