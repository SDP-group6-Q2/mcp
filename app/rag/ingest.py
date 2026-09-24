"""Index the manual PDFs into the RAG database. Idempotent: unchanged manuals are skipped.

    python -m app.rag.ingest                         # every manual in the Supabase bucket
    python -m app.rag.ingest --from-dir DIR          # PDFs from a local folder (development)
    python -m app.rag.ingest --serial 15610 --force  # re-index one manual even if unchanged
"""

import argparse
import asyncio
import hashlib
import logging
from pathlib import Path

import psycopg

from app.config import settings
from app.rag import db, embeddings
from app.rag.chunking import CHUNKER_VERSION, chunk_manual
from app.rag.pdf import parse_pdf, searchable_pages
from app.rag.sources import ManualFile, bucket_manuals, local_manuals

logger = logging.getLogger(__name__)

_EMBED_BATCH = 64


async def _is_current(conn: psycopg.AsyncConnection, manual: ManualFile, sha256: str) -> bool:
    cursor = await conn.execute(
        """
        SELECT 1 FROM manual_index
        WHERE serial_number = %s AND content_sha256 = %s AND embedding_model = %s AND chunker_version = %s
        """,
        (manual.serial_number, sha256, settings.embedding_model, CHUNKER_VERSION),
    )
    return await cursor.fetchone() is not None


async def index_manual(conn: psycopg.AsyncConnection, manual: ManualFile, force: bool = False) -> str:
    """Index one manual. Returns 'skipped' or a short summary of what was indexed."""
    sha256 = hashlib.sha256(manual.data).hexdigest()
    if not force and await _is_current(conn, manual, sha256):
        return "skipped (unchanged)"

    parsed = await asyncio.to_thread(parse_pdf, manual.data)
    chunks = chunk_manual(searchable_pages(parsed.pages), parsed.outline)
    if not chunks:
        raise RuntimeError(f"{manual.filename}: no extractable text")

    vectors: list[list[float]] = []
    for start in range(0, len(chunks), _EMBED_BATCH):
        batch = chunks[start : start + _EMBED_BATCH]
        vectors.extend(await embeddings.embed_passages([chunk.embedding_text for chunk in batch]))

    # One transaction: readers never see a half-indexed manual.
    async with conn.transaction():
        await conn.execute("DELETE FROM manual_index WHERE serial_number = %s", (manual.serial_number,))
        await conn.execute(
            """
            INSERT INTO manual_index
                (serial_number, source, content_sha256, embedding_model, chunker_version, page_count, chunk_count)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                manual.serial_number,
                manual.filename,
                sha256,
                settings.embedding_model,
                CHUNKER_VERSION,
                len(parsed.pages),
                len(chunks),
            ),
        )
        async with conn.cursor() as cursor:
            await cursor.executemany(
                """
                INSERT INTO manual_chunks
                    (serial_number, section_number, section_title, section_path,
                     page_start, page_end, content, embedding)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    (
                        manual.serial_number,
                        chunk.section_number,
                        chunk.section_title,
                        chunk.section_path,
                        chunk.page_start,
                        chunk.page_end,
                        chunk.content,
                        vector,
                    )
                    for chunk, vector in zip(chunks, vectors)
                ],
            )
    # The current-check above opened an implicit transaction, which made the block above a savepoint:
    # without this commit everything would be rolled back when the connection closes.
    await conn.commit()
    return f"indexed {len(chunks)} chunks from {len(parsed.pages)} pages"


async def main(args: argparse.Namespace) -> None:
    if args.from_dir:
        manuals = list(local_manuals(Path(args.from_dir), args.serial))
    else:
        manuals = await bucket_manuals(args.serial)
    if not manuals:
        logger.warning("No manuals found to index.")
        return

    conn = await db.connect_for_ingest()
    try:
        for manual in manuals:
            result = await index_manual(conn, manual, force=args.force)
            logger.info("%s (serial %s): %s", manual.filename, manual.serial_number, result)
    finally:
        await conn.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    parser = argparse.ArgumentParser(description="Index the manual PDFs for retrieval.")
    parser.add_argument("--from-dir", help="Read PDFs from a local folder instead of the Supabase bucket.")
    parser.add_argument("--serial", help="Only this manual's serial number.")
    parser.add_argument("--force", action="store_true", help="Re-index even if unchanged.")
    asyncio.run(main(parser.parse_args()))
