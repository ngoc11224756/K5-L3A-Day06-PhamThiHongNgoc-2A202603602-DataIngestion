"""Store and search vectors using PostgreSQL + pgvector."""
from typing import Any
import numpy as np

import psycopg
from pgvector.psycopg import register_vector
from psycopg.types.json import Json

from .models import Chunk

_ALLOWED_FILTER_FIELDS = {"chuong"}


class PgVectorStore:
    def __init__(self, database_url: str, dimensions: int) -> None:
        self.database_url = database_url
        self.dimensions = dimensions
        self._conn = psycopg.connect(database_url, autocommit=True)
        register_vector(self._conn)

    def create_schema(self) -> None:
        with self._conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
            cur.execute(
                f"""
                CREATE TABLE IF NOT EXISTS chunks (
                    config TEXT NOT NULL,
                    chunk_id TEXT NOT NULL,
                    document_id TEXT NOT NULL,
                    source TEXT NOT NULL,
                    page INTEGER NOT NULL,
                    chuong INTEGER,
                    content TEXT NOT NULL,
                    metadata JSONB NOT NULL DEFAULT '{{}}'::jsonb,
                    embedding VECTOR({self.dimensions}) NOT NULL,
                    PRIMARY KEY (config, chunk_id)
                )
                """
            )

            cur.execute(
                "CREATE INDEX IF NOT EXISTS chunks_config_document_idx "
                "ON chunks (config, document_id)"
            )

    def upsert(self, strategy: str, chunks: list[Chunk], vectors: list[list[float]]) -> None:
        """Ghi chunk theo ID ổn định (config, chunk_id); nạp lại không nhân đôi.

        Sau khi insert/update, xóa các chunk cũ của cùng document_id + strategy
        mà không còn xuất hiện trong lần nạp này (xử lý trường hợp tài liệu đổi
        khiến số lượng/ranh giới chunk thay đổi).
        """
        if len(chunks) != len(vectors):
            raise ValueError("Số chunk và số vector phải bằng nhau")
        for v in vectors:
            if len(v) != self.dimensions:
                raise ValueError(f"Vector chiều {len(v)}, kỳ vọng {self.dimensions}")

        document_ids = {c.document_id for c in chunks}
        current_ids = [c.chunk_id for c in chunks]

        with self._conn.cursor() as cur:
            for chunk, vector in zip(chunks, vectors):
                cur.execute(
                    """
                    INSERT INTO chunks
                        (config, chunk_id, document_id, source, page, chuong,
                         content, metadata, embedding)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (config, chunk_id) DO UPDATE SET
                        document_id = EXCLUDED.document_id,
                        source = EXCLUDED.source,
                        page = EXCLUDED.page,
                        chuong = EXCLUDED.chuong,
                        content = EXCLUDED.content,
                        metadata = EXCLUDED.metadata,
                        embedding = EXCLUDED.embedding
                    """,
                    (
                        strategy,
                        chunk.chunk_id,
                        chunk.document_id,
                        chunk.source,
                        chunk.page,
                        chunk.metadata.get("chuong"),
                        chunk.text,
                        Json(chunk.metadata),
                        vector,
                    ),
                )

            for document_id in document_ids:
                cur.execute(
                    """
                    DELETE FROM chunks
                    WHERE config = %s AND document_id = %s AND NOT (chunk_id = ANY(%s))
                    """,
                    (strategy, document_id, current_ids),
                )

    def search(
        self,
        strategy: str,
        query_vector: list[float],
        top_k: int = 3,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        if len(query_vector) != self.dimensions:
            raise ValueError(
                f"Query vector chiều {len(query_vector)}, kỳ vọng {self.dimensions}"
            )

        where_clauses = ["config = %(strategy)s"]
        params: dict[str, Any] = {
            "strategy": strategy,
            "qvec": np.asarray(query_vector, dtype=np.float32),
            "k": top_k,
        }

        if filters:
            for key, value in filters.items():
                if key not in _ALLOWED_FILTER_FIELDS:
                    raise ValueError(f"Trường filter không được phép: {key}")
                where_clauses.append(f"{key} = %({key})s")
                params[key] = value

        where_sql = " AND ".join(where_clauses)

        with self._conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT chunk_id,document_id, content, source, page, chuong, metadata,
                       embedding <=> %(qvec)s AS distance
                FROM chunks
                WHERE {where_sql}
                ORDER BY embedding <=> %(qvec)s
                LIMIT %(k)s
                """,
                params,
            )
            rows = cur.fetchall()
            columns = [desc.name for desc in cur.description]

        return [dict(zip(columns, row)) for row in rows]