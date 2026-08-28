"""SQLite veri katmanı: chunk metni + embedding vektörü tek dosyada.

Embedding float32 BLOB olarak saklanır (float64'ün yarısı yer kaplar; benzerlik
sıralaması için fazlasıyla yeterli). Yaz->oku turunun vektörü bozmadığı test edilir.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable, NamedTuple

import numpy as np

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    source       TEXT    NOT NULL,
    chunk_index  INTEGER NOT NULL,
    content      TEXT    NOT NULL,
    embedding    BLOB    NOT NULL,
    dim          INTEGER NOT NULL,
    created_at   TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE (source, chunk_index)
);
CREATE INDEX IF NOT EXISTS idx_documents_source ON documents(source);
"""


class Chunk(NamedTuple):
    """Veritabanından okunan bir kayıt."""

    id: int
    source: str
    chunk_index: int
    content: str
    embedding: np.ndarray


def connect(db_path: Path | str | None = None) -> sqlite3.Connection:
    """Bağlantı aç ve şemayı garanti et. ':memory:' testler için geçerli bir yoldur."""
    path = Path(db_path) if db_path is not None else config.DB_PATH
    if str(path) != ":memory:":
        path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.executescript(SCHEMA)
    return conn


def to_blob(vector: Iterable[float]) -> bytes:
    return np.asarray(list(vector), dtype=np.float32).tobytes()


def from_blob(blob: bytes) -> np.ndarray:
    return np.frombuffer(blob, dtype=np.float32)


def upsert_chunk(
    conn: sqlite3.Connection,
    source: str,
    chunk_index: int,
    content: str,
    embedding: Iterable[float],
) -> None:
    """Aynı (source, chunk_index) tekrar gelirse üzerine yazar — ingest tekrar
    çalıştırılabilir olsun diye (idempotent)."""
    vec = np.asarray(list(embedding), dtype=np.float32)
    conn.execute(
        """
        INSERT INTO documents (source, chunk_index, content, embedding, dim)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(source, chunk_index) DO UPDATE SET
            content   = excluded.content,
            embedding = excluded.embedding,
            dim       = excluded.dim
        """,
        (source, chunk_index, content, vec.tobytes(), int(vec.size)),
    )


def all_chunks(conn: sqlite3.Connection) -> list[Chunk]:
    rows = conn.execute(
        "SELECT id, source, chunk_index, content, embedding FROM documents ORDER BY source, chunk_index"
    ).fetchall()
    return [Chunk(r[0], r[1], r[2], r[3], from_blob(r[4])) for r in rows]


def count(conn: sqlite3.Connection) -> int:
    return int(conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0])


def sources(conn: sqlite3.Connection) -> list[tuple[str, int]]:
    return [
        (r[0], int(r[1]))
        for r in conn.execute(
            "SELECT source, COUNT(*) FROM documents GROUP BY source ORDER BY source"
        ).fetchall()
    ]


def delete_source(conn: sqlite3.Connection, source: str) -> int:
    cur = conn.execute("DELETE FROM documents WHERE source = ?", (source,))
    return cur.rowcount


def clear(conn: sqlite3.Connection) -> None:
    conn.execute("DELETE FROM documents")
