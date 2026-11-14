"""Store and search vectors using PostgreSQL + pgvector."""
import json
from typing import Any
import psycopg
from pgvector.psycopg import register_vector

from .models import Chunk


class PgVectorStore:
    def __init__(self, database_url: str, dimensions: int) -> None:
        """Retain connection settings; validate model dimensions."""
        self.database_url = database_url
        self.dimensions = dimensions

    def _get_connection(self):
        """Helper to get a configured database connection."""
        conn = psycopg.connect(self.database_url, autocommit=True)
        # Register pgvector extension types with psycopg
        try:
            conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            register_vector(conn)
        except psycopg.errors.InsufficientPrivilege:
            pass # Extension might already exist, or needs superuser
        return conn

    def create_schema(self) -> None:
        """Create table with vector column and metadata."""
        query = f"""
        CREATE TABLE IF NOT EXISTS chunks (
            chunk_id VARCHAR(64) PRIMARY KEY,
            document_id VARCHAR(255) NOT NULL,
            source VARCHAR(255) NOT NULL,
            page INTEGER NOT NULL,
            text TEXT NOT NULL,
            strategy VARCHAR(50) NOT NULL,
            metadata JSONB NOT NULL DEFAULT '{{}}'::jsonb,
            embedding VECTOR({self.dimensions})
        );
        -- Indexes for faster filtering and vector search
        CREATE INDEX IF NOT EXISTS idx_chunks_strategy ON chunks(strategy);
        CREATE INDEX IF NOT EXISTS idx_chunks_metadata ON chunks USING GIN (metadata);
        """
        with self._get_connection() as conn:
            conn.execute(query)

    def count(self, strategy: str) -> int:
        """Count the number of stored chunks for a given strategy."""
        query = "SELECT COUNT(*) FROM chunks WHERE strategy = %s;"
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (strategy,))
                row = cur.fetchone()
                return row[0] if row else 0

    def upsert(self, strategy: str, chunks: list[Chunk], vectors: list[list[float]]) -> None:
        """Write stable IDs without duplicates using ON CONFLICT DO UPDATE."""
        if len(chunks) != len(vectors):
            raise ValueError("Number of chunks and vectors must match.")

        query = """
        INSERT INTO chunks (chunk_id, document_id, source, page, text, strategy, metadata, embedding)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (chunk_id) DO UPDATE SET
            metadata = EXCLUDED.metadata,
            embedding = EXCLUDED.embedding;
        """

        records = [
            (
                chunk.chunk_id,
                chunk.document_id,
                chunk.source,
                chunk.page,
                chunk.text,
                strategy,
                json.dumps(chunk.metadata),
                vector
            )
            for chunk, vector in zip(chunks, vectors)
        ]

        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.executemany(query, records)

    def search(
        self, strategy: str, query_vector: list[float], top_k: int = 3,
        filters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Filter permitted metadata in SQL, rank by cosine distance (<=>)."""

        # Base query filters for strategy
        sql_filters = ["strategy = %s"]
        params: list[Any] = [strategy]

        # Dynamically build JSONB filter if metadata filters are provided (Config C)
        if filters:
            sql_filters.append("metadata @> %s::jsonb")
            params.append(json.dumps(filters))

        filter_clause = " AND ".join(sql_filters)

        # Cosine distance operator is `<=>`
        query = f"""
        SELECT chunk_id, document_id, source, page, text, metadata,
               (embedding <=> %s::vector) AS score
        FROM chunks
        WHERE {filter_clause}
        ORDER BY score ASC
        LIMIT %s;
        """

        # Prepend vector to params, append top_k
        params.insert(0, query_vector)
        params.append(top_k)

        results = []
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                rows = cur.fetchall()
                for row in rows:
                    results.append({
                        "chunk_id": row[0],
                        "document_id": row[1],
                        "source": row[2],
                        "page": row[3],
                        "text": row[4],
                        "metadata": row[5],
                        "score": float(row[6]) # Closer to 0 is better for distance
                    })
        return results