"""Ingestion: corpus klasöründeki belgeleri chunk'la, embed et, SQLite'a yaz."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Callable, NamedTuple

from . import chunking, db


class IngestReport(NamedTuple):
    files: int
    chunks: int
    skipped: list[tuple[str, str]]  # (dosya, sebep)

    def summary(self) -> str:
        line = f"{self.files} dosya, {self.chunks} chunk yazıldı."
        if self.skipped:
            line += f" {len(self.skipped)} dosya atlandı."
        return line


def ingest_corpus(
    client,
    conn: sqlite3.Connection,
    corpus_dir: Path | None = None,
    batch_size: int = 16,
    progress: Callable[[str], None] | None = None,
) -> IngestReport:
    """Klasördeki tüm belgeleri işle.

    Aynı dosya tekrar işlenirse kayıtların üzerine yazılır (idempotent), ancak
    dosya kısaldıysa artık üretilmeyen eski chunk'lar da silinir — yoksa
    veritabanında hiçbir belgeye ait olmayan hayalet parçalar kalırdı.
    """
    files = chunking.iter_corpus_files(corpus_dir)
    say = progress or (lambda _msg: None)

    total_chunks = 0
    skipped: list[tuple[str, str]] = []
    processed_files = 0

    for path in files:
        try:
            source, chunks = chunking.chunk_file(path, corpus_dir)
        except Exception as exc:
            skipped.append((path.name, str(exc)))
            say(f"  ATLANDI {path.name}: {exc}")
            continue

        if not chunks:
            skipped.append((path.name, "metin çıkarılamadı / boş"))
            say(f"  ATLANDI {path.name}: boş")
            continue

        say(f"  {source}: {len(chunks)} chunk")
        for start in range(0, len(chunks), batch_size):
            batch = chunks[start : start + batch_size]
            vectors = client.embed(batch)
            if len(vectors) != len(batch):
                raise RuntimeError(
                    f"Embedding sayısı chunk sayısıyla uyuşmuyor: {len(vectors)} != {len(batch)}"
                )
            for offset, (content, vector) in enumerate(zip(batch, vectors)):
                db.upsert_chunk(conn, source, start + offset, content, vector)

        # Dosya kısaldıysa fazlalıkları temizle.
        conn.execute(
            "DELETE FROM documents WHERE source = ? AND chunk_index >= ?",
            (source, len(chunks)),
        )
        conn.commit()

        processed_files += 1
        total_chunks += len(chunks)

    return IngestReport(processed_files, total_chunks, skipped)
