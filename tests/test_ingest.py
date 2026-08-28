"""Ingestion boru hattı testleri — sahte istemciyle."""

from __future__ import annotations

from foundry_rag import db
from foundry_rag.ingest import ingest_corpus
from conftest import FakeClient


VOCAB = ["alfa", "beta", "gama"]


def test_klasordeki_belgeler_veritabanina_yazilir(conn, tmp_path):
    (tmp_path / "bir.md").write_text("Alfa hakkında.\n\nBeta hakkında.", encoding="utf-8")
    (tmp_path / "iki.txt").write_text("Gama hakkında.", encoding="utf-8")

    report = ingest_corpus(FakeClient(VOCAB), conn, corpus_dir=tmp_path)

    assert report.files == 2
    assert db.count(conn) == report.chunks
    assert dict(db.sources(conn)) == {"bir.md": report.chunks - 1, "iki.txt": 1}


def test_tekrar_calistirmak_kayit_sayisini_artirmaz(conn, tmp_path):
    (tmp_path / "a.md").write_text("Alfa.\n\nBeta.", encoding="utf-8")
    client = FakeClient(VOCAB)

    ilk = ingest_corpus(client, conn, corpus_dir=tmp_path)
    ikinci = ingest_corpus(client, conn, corpus_dir=tmp_path)

    assert ilk.chunks == ikinci.chunks
    assert db.count(conn) == ilk.chunks


def test_dosya_kisalirsa_eski_chunklar_silinir(conn, tmp_path):
    """Hayalet parça bırakma testi: uzun belge kısalınca fazlalık kalmamalı."""
    path = tmp_path / "a.md"
    path.write_text("\n\n".join(f"Alfa {i}. " + "dolgu " * 200 for i in range(4)), encoding="utf-8")
    client = FakeClient(VOCAB)

    uzun = ingest_corpus(client, conn, corpus_dir=tmp_path)
    assert uzun.chunks > 1

    path.write_text("Alfa tek paragraf.", encoding="utf-8")
    kisa = ingest_corpus(client, conn, corpus_dir=tmp_path)

    assert kisa.chunks == 1
    assert db.count(conn) == 1, "eski chunk'lar veritabanında kaldı"


def test_bos_dosya_atlanir_ve_raporlanir(conn, tmp_path):
    (tmp_path / "dolu.md").write_text("Alfa.", encoding="utf-8")
    (tmp_path / "bos.md").write_text("   \n\n  ", encoding="utf-8")

    report = ingest_corpus(FakeClient(VOCAB), conn, corpus_dir=tmp_path)

    assert report.files == 1
    assert [ad for ad, _ in report.skipped] == ["bos.md"]


def test_bos_klasor(conn, tmp_path):
    report = ingest_corpus(FakeClient(VOCAB), conn, corpus_dir=tmp_path)
    assert report.files == 0 and report.chunks == 0


def test_embedding_metnine_kaynak_adi_eklenir():
    """Vektör kaynak adıyla birlikte üretilir, saklanan içerik değişmez."""
    from foundry_rag.ingest import embedding_metni

    metin = embedding_metni("ders/hafta7.md", "Final sınavı B-204'te.")
    assert metin.startswith("ders/hafta7.md")
    assert "Final sınavı B-204'te." in metin


def test_kaynak_adi_veritabanina_sizmaz(conn, tmp_path):
    """Ön ek YALNIZCA embedding'e girer; kullanıcıya gösterilen metne değil."""
    (tmp_path / "a.md").write_text("Alfa hakkında bilgi.", encoding="utf-8")
    client = FakeClient(VOCAB)

    ingest_corpus(client, conn, corpus_dir=tmp_path)

    (chunk,) = db.all_chunks(conn)
    assert chunk.content == "Alfa hakkında bilgi."
    assert "a.md" not in chunk.content


def test_farkli_kaynaklar_farkli_vektor_uretir(conn, tmp_path):
    """Aynı metin iki farklı dosyada farklı vektör almalı — ayrım buradan geliyor."""
    from foundry_rag.ingest import embedding_metni

    client = FakeClient(["alfa", "birinci", "ikinci"])
    v1 = client.embed_one(embedding_metni("birinci.md", "Alfa."))
    v2 = client.embed_one(embedding_metni("ikinci.md", "Alfa."))
    assert v1 != v2
