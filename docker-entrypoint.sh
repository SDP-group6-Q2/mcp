#!/bin/sh
# Starts the MCP server. In the background it first makes sure the manuals are indexed for search
# (the RAG database is created if missing, and manuals that haven't changed are skipped), so the
# server is available immediately; until a manual is indexed its tool says so explicitly.
set -e

if [ "${AUTO_INGEST:-true}" = "true" ]; then
    (
        if [ -n "$SUPABASE_URL" ] && [ -n "$SUPABASE_SERVICE_ROLE_KEY" ]; then
            echo "init: indexing manuals from the Supabase bucket"
            python -m app.rag.ingest
        elif [ -d /data/manuals ]; then
            echo "init: no Supabase credentials; indexing manuals from /data/manuals"
            python -m app.rag.ingest --from-dir /data/manuals
        else
            echo "init: no manual source configured, skipping manual indexing"
        fi || echo "init: WARNING: manual indexing failed; run 'python -m app.rag.ingest' to retry"
    ) &
fi

exec "$@"
