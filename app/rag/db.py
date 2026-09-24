"""Connections to the RAG database (its own database on the shared Postgres instance)."""

from pathlib import Path

import psycopg
from pgvector.psycopg import register_vector_async
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo

from app.config import settings

_SCHEMA = (Path(__file__).parent / "schema.sql").read_text()


def _database_name() -> str:
    return conninfo_to_dict(settings.rag_database_url).get("dbname") or "rag"


async def ensure_database() -> None:
    """Create the RAG database if it doesn't exist yet (needs CREATEDB on the server)."""
    admin_url = make_conninfo(settings.rag_database_url, dbname="postgres")
    async with await psycopg.AsyncConnection.connect(admin_url, autocommit=True) as conn:
        cursor = await conn.execute("SELECT 1 FROM pg_database WHERE datname = %s", (_database_name(),))
        if await cursor.fetchone() is None:
            # template0: unlike template1 it carries no collation version, so this still works when the
            # server's OS libraries changed since the cluster was created.
            await conn.execute(
                sql.SQL("CREATE DATABASE {} TEMPLATE template0").format(sql.Identifier(_database_name()))
            )


async def apply_schema(conn: psycopg.AsyncConnection) -> None:
    await conn.execute(_SCHEMA)
    await conn.commit()


async def connect() -> psycopg.AsyncConnection:
    """Connection with the vector type registered. The database and schema must already exist."""
    conn = await psycopg.AsyncConnection.connect(settings.rag_database_url)
    await register_vector_async(conn)
    return conn


async def connect_for_ingest() -> psycopg.AsyncConnection:
    """Create the database and schema if needed, then connect."""
    await ensure_database()
    bootstrap = await psycopg.AsyncConnection.connect(settings.rag_database_url)
    try:
        await apply_schema(bootstrap)
    finally:
        await bootstrap.close()
    return await connect()
