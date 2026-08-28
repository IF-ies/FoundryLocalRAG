"""SQLite katmanı testleri."""

from __future__ import annotations

import numpy as np

from foundry_rag import db


def test_yaz_oku_turu_vektoru_bozmaz(conn):
    vector = [0.1, -0.25, 3.5, 0.0, -1.0]
    db.upsert_chunk(conn, "a.md", 0, "içerik", vector)
    conn.commit()

    (chunk,) = db.all_chunks(conn)
    # float32'ye yuvarlama var; eşitlik değil tolerans beklenir.
    assert np.allclose(chunk.embedding, np.array(vector, dtype=np.float32), atol=1e-6)
    assert chunk.embedding.dtype == np.float32
    assert chunk.content == "içerik"
    assert chunk.source == "a.md"


def test_turkce_karakterler_korunur(conn):
    metin = "Şu ĞİÖÇÜ ışıklı yazı — çöğüşı"
    db.upsert_chunk(conn, "tr.md", 0, metin, [1.0])
    conn.commit()
    (chunk,) = db.all_chunks(conn)
    assert chunk.content == metin


def test_ayni_kaynak_ve_index_uzerine_yazar(conn):
    db.upsert_chunk(conn, "a.md", 0, "eski", [1.0, 0.0])
    db.upsert_chunk(conn, "a.md", 0, "yeni", [0.0, 1.0])
    conn.commit()

    assert db.count(conn) == 1
    (chunk,) = db.all_chunks(conn)
    assert chunk.content == "yeni"
    assert np.allclose(chunk.embedding, [0.0, 1.0])


def test_siralama_kaynak_ve_index_bazli(conn):
    db.upsert_chunk(conn, "b.md", 0, "b0", [1.0])
    db.upsert_chunk(conn, "a.md", 1, "a1", [1.0])
    db.upsert_chunk(conn, "a.md", 0, "a0", [1.0])
    conn.commit()

    assert [c.content for c in db.all_chunks(conn)] == ["a0", "a1", "b0"]


def test_kaynak_ozeti_ve_silme(conn):
    db.upsert_chunk(conn, "a.md", 0, "x", [1.0])
    db.upsert_chunk(conn, "a.md", 1, "y", [1.0])
    db.upsert_chunk(conn, "b.md", 0, "z", [1.0])
    conn.commit()

    assert db.sources(conn) == [("a.md", 2), ("b.md", 1)]
    assert db.delete_source(conn, "a.md") == 2
    assert db.count(conn) == 1


def test_bos_veritabani(conn):
    assert db.count(conn) == 0
    assert db.all_chunks(conn) == []
    assert db.sources(conn) == []
