"""Retrieval testleri.

Beklenen benzerlik değerleri ELDE hesaplanmıştır — kodun formülü tekrar
yazılmaz. Aksi halde formül yanlış olsa bile test yeşil kalırdı.
"""

from __future__ import annotations

import math

import pytest

from foundry_rag import db
from foundry_rag.retrieval import cosine_similarity, rank


def _chunk(idx: int, source: str, content: str, embedding: list[float]) -> db.Chunk:
    return db.Chunk(idx, source, 0, content, db.from_blob(db.to_blob(embedding)))


def test_ayni_vektor_bir():
    assert cosine_similarity([1.0, 2.0, 3.0], [1.0, 2.0, 3.0]) == pytest.approx(1.0)


def test_dik_vektorler_sifir():
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)


def test_zit_vektorler_eksi_bir():
    assert cosine_similarity([1.0, 0.0], [-1.0, 0.0]) == pytest.approx(-1.0)


def test_elde_hesaplanmis_deger():
    # a=(1,1), b=(1,0) -> dot=1, |a|=sqrt(2), |b|=1 -> 1/sqrt(2)
    assert cosine_similarity([1.0, 1.0], [1.0, 0.0]) == pytest.approx(1 / math.sqrt(2))


def test_olcek_degisimi_sonucu_degistirmez():
    assert cosine_similarity([1.0, 1.0], [5.0, 5.0]) == pytest.approx(1.0)


def test_sifir_vektor_sifir_doner_bolme_hatasi_yok():
    assert cosine_similarity([0.0, 0.0], [1.0, 1.0]) == 0.0


def test_boyut_uyusmazligi_hata():
    with pytest.raises(ValueError):
        cosine_similarity([1.0, 2.0], [1.0])


def test_siralama_en_yakini_basa_koyar():
    chunks = [
        _chunk(1, "uzak.md", "uzak", [0.0, 1.0]),
        _chunk(2, "yakin.md", "yakın", [1.0, 0.0]),
        _chunk(3, "orta.md", "orta", [1.0, 1.0]),
    ]
    hits = rank([1.0, 0.0], chunks, top_k=3, min_similarity=-1.0)
    assert [h.chunk.source for h in hits] == ["yakin.md", "orta.md", "uzak.md"]
    assert hits[0].score == pytest.approx(1.0)
    assert hits[1].score == pytest.approx(1 / math.sqrt(2))


def test_top_k_sinirlar():
    chunks = [_chunk(i, f"{i}.md", "x", [1.0, 0.0]) for i in range(5)]
    assert len(rank([1.0, 0.0], chunks, top_k=2, min_similarity=-1.0)) == 2


def test_esik_altindakiler_elenir():
    chunks = [
        _chunk(1, "iyi.md", "iyi", [1.0, 0.0]),
        _chunk(2, "kotu.md", "kötü", [0.0, 1.0]),
    ]
    hits = rank([1.0, 0.0], chunks, top_k=5, min_similarity=0.5)
    assert [h.chunk.source for h in hits] == ["iyi.md"]


def test_hicbiri_esigi_gecmezse_bos_doner():
    chunks = [_chunk(1, "a.md", "a", [0.0, 1.0])]
    assert rank([1.0, 0.0], chunks, top_k=3, min_similarity=0.5) == []


def test_bos_chunk_listesi():
    assert rank([1.0, 0.0], [], top_k=3) == []
