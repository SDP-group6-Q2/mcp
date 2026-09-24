"""Hybrid retrieval over one manual: vector + full-text candidates, rank-fused, then reranked."""

import re
from dataclasses import dataclass

import psycopg

from app.rag import embeddings

CANDIDATES_PER_METHOD = 20
TOP_K = 5
_RRF_K = 60  # reciprocal rank fusion damping constant
_ALARM_CODE_PREFIX = re.compile(r"\bAL\d{3}_", re.IGNORECASE)


@dataclass(frozen=True)
class Excerpt:
    section_number: str
    section_title: str
    section_path: str
    page_start: int
    page_end: int
    content: str
    score: float


def normalise_query(query: str) -> str:
    """Alarm codes look like 'AL017_LOW_AIR_PRESSURE' but the manuals only describe the condition, so
    the numeric prefix is dropped and underscores become spaces."""
    return " ".join(_ALARM_CODE_PREFIX.sub("", query).replace("_", " ").split())


def lexical_query(query: str) -> str:
    """OR-joined tsquery from the query's words: natural-language questions rarely match all their words."""
    tokens = dict.fromkeys(re.findall(r"[A-Za-z0-9]{2,}", query.lower()))
    return " | ".join(tokens)


def reciprocal_rank_fusion(rankings: list[list[int]]) -> list[int]:
    """Merge ranked lists of ids: an id scores 1/(k + rank) in each list it appears in."""
    scores: dict[int, float] = {}
    for ranking in rankings:
        for rank, chunk_id in enumerate(ranking, start=1):
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (_RRF_K + rank)
    return sorted(scores, key=scores.__getitem__, reverse=True)


async def is_indexed(conn: psycopg.AsyncConnection, serial_number: str) -> bool:
    cursor = await conn.execute("SELECT 1 FROM manual_index WHERE serial_number = %s", (serial_number,))
    return await cursor.fetchone() is not None


async def search_manual(
    conn: psycopg.AsyncConnection, serial_number: str, query: str, top_k: int = TOP_K
) -> list[Excerpt]:
    query = normalise_query(query)
    query_embedding = await embeddings.embed_query(query)

    vector_cursor = await conn.execute(
        """
        SELECT id FROM manual_chunks WHERE serial_number = %s
        ORDER BY embedding <=> %s::vector LIMIT %s
        """,
        (serial_number, query_embedding, CANDIDATES_PER_METHOD),
    )
    vector_ids = [row[0] for row in await vector_cursor.fetchall()]

    lexical_ids: list[int] = []
    tsquery = lexical_query(query)
    if tsquery:
        text_cursor = await conn.execute(
            """
            SELECT id FROM manual_chunks, to_tsquery('english', %s) AS q
            WHERE serial_number = %s AND tsv @@ q
            ORDER BY ts_rank_cd(tsv, q) DESC LIMIT %s
            """,
            (tsquery, serial_number, CANDIDATES_PER_METHOD),
        )
        lexical_ids = [row[0] for row in await text_cursor.fetchall()]

    fused = reciprocal_rank_fusion([vector_ids, lexical_ids])
    if not fused:
        return []

    rows_cursor = await conn.execute(
        """
        SELECT id, section_number, section_title, section_path, page_start, page_end, content
        FROM manual_chunks WHERE id = ANY(%s)
        """,
        (fused,),
    )
    by_id = {row[0]: row for row in await rows_cursor.fetchall()}
    candidates = [by_id[chunk_id] for chunk_id in fused if chunk_id in by_id]

    scores = await embeddings.rerank(query, [f"{row[3]}\n{row[6]}" for row in candidates])
    ranked = sorted(zip(candidates, scores), key=lambda pair: pair[1], reverse=True)[:top_k]
    return [
        Excerpt(row[1], row[2], row[3], row[4], row[5], row[6], score) for row, score in ranked
    ]
