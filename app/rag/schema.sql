-- Manuals RAG schema. Idempotent: safe to run on every ingest. The data is derived from the PDFs, so it
-- can be dropped and rebuilt at any time (python -m app.rag.ingest --force).
CREATE EXTENSION IF NOT EXISTS vector;

-- One row per indexed manual; lets ingest skip manuals whose PDF, embedding model and chunker are unchanged.
CREATE TABLE IF NOT EXISTS manual_index (
    serial_number   TEXT PRIMARY KEY,
    source          TEXT NOT NULL,
    content_sha256  TEXT NOT NULL,
    embedding_model TEXT NOT NULL,
    chunker_version TEXT NOT NULL,
    page_count      INTEGER NOT NULL,
    chunk_count     INTEGER NOT NULL,
    indexed_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Keyed by the manual's serial number: no company or user data lives here (access is checked by the API).
CREATE TABLE IF NOT EXISTS manual_chunks (
    id             BIGSERIAL PRIMARY KEY,
    serial_number  TEXT NOT NULL REFERENCES manual_index (serial_number) ON DELETE CASCADE,
    section_number TEXT NOT NULL,
    section_title  TEXT NOT NULL,
    section_path   TEXT NOT NULL,
    page_start     INTEGER NOT NULL,
    page_end       INTEGER NOT NULL,
    content        TEXT NOT NULL,
    tsv            TSVECTOR GENERATED ALWAYS AS (
                       to_tsvector('english', section_path || ' ' || content)
                   ) STORED,
    embedding      VECTOR(768) NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_manual_chunks_serial ON manual_chunks (serial_number);
CREATE INDEX IF NOT EXISTS ix_manual_chunks_tsv ON manual_chunks USING GIN (tsv);
-- No ANN index: every search is filtered to one manual (a few hundred rows), so an exact scan is fast.
