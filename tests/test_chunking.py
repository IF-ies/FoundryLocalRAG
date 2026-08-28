"""Chunk'lama testleri — model gerektirmez."""

from __future__ import annotations

import pytest

from foundry_rag import chunking


def test_bos_metin_bos_liste():
    assert chunking.chunk_text("") == []
    assert chunking.chunk_text("   \n\n  \n ") == []


def test_kisa_metin_tek_chunk():
    chunks = chunking.chunk_text("Tek paragraf.", max_chars=100, overlap_chars=0)
    assert chunks == ["Tek paragraf."]


def test_paragraflar_sinira_kadar_birlestirilir():
    text = "\n\n".join(["A" * 40, "B" * 40, "C" * 40])
    chunks = chunking.chunk_text(text, max_chars=100, overlap_chars=0)
    # 40+2+40 = 82 sığar, üçüncüsü 124 olurdu -> ikinci chunk'a düşer.
    assert len(chunks) == 2
    assert chunks[0].startswith("A") and "B" in chunks[0]
    assert chunks[1].startswith("C")


def test_hicbir_chunk_siniri_asmaz():
    text = "\n\n".join(f"Paragraf {i}. " + "kelime " * 60 for i in range(10))
    chunks = chunking.chunk_text(text, max_chars=300, overlap_chars=50)
    assert chunks, "chunk üretilmedi"
    assert all(len(c) <= 300 for c in chunks), [len(c) for c in chunks]


def test_tek_dev_paragraf_bolunur_ve_kaybolmaz():
    paragraph = ". ".join(f"Cumle {i} burada" for i in range(80))
    chunks = chunking.chunk_text(paragraph, max_chars=200, overlap_chars=0)
    assert len(chunks) > 1
    # Örnekleme yerine gerçek kayıp kontrolü: her cümle bir yerde geçmeli.
    birlesik = " ".join(chunks)
    for i in (0, 40, 79):
        assert f"Cumle {i} burada" in birlesik


def test_overlap_onceki_baglami_tasir():
    # 3 x 40 karakter: ilk chunk A+B'yi alır, C taşar -> ikinci chunk
    # birincinin son 20 karakteriyle (B'nin kuyruğu) başlamalı.
    text = "\n\n".join(["A" * 40, "B" * 40, "C" * 40])
    chunks = chunking.chunk_text(text, max_chars=100, overlap_chars=20)
    assert len(chunks) == 2
    assert chunks[1].startswith("B" * 20)
    assert chunks[1].endswith("C" * 40)


def test_overlap_sigmazsa_dusurulur_sinir_asilmaz():
    """Kuyruk eklenince üst sınır aşılacaksa overlap tamamen düşürülür.

    Yarım kelimelik kuyruk uğruna sınırı aşmaktansa bağlamı feda ediyoruz;
    'hiçbir chunk max_chars'ı aşmaz' garantisi daha değerli.
    """
    text = "\n\n".join(["X" * 90, "Y" * 90])
    chunks = chunking.chunk_text(text, max_chars=100, overlap_chars=20)
    assert chunks == ["X" * 90, "Y" * 90]


def test_overlap_max_chars_esit_veya_buyukse_hata():
    with pytest.raises(ValueError):
        chunking.chunk_text("abc", max_chars=10, overlap_chars=10)


def test_desteklenmeyen_dosya_turu(tmp_path):
    path = tmp_path / "resim.png"
    path.write_bytes(b"\x89PNG")
    with pytest.raises(ValueError):
        chunking.read_text(path)


def test_corpus_taramasi_sadece_desteklenenleri_alir(tmp_path):
    (tmp_path / "a.md").write_text("A", encoding="utf-8")
    (tmp_path / "b.txt").write_text("B", encoding="utf-8")
    (tmp_path / "c.png").write_bytes(b"x")
    (tmp_path / "alt").mkdir()
    (tmp_path / "alt" / "d.md").write_text("D", encoding="utf-8")

    # Sıra göreli YOLA göre kararlıdır (alt/d.md, b.txt'ten önce gelir),
    # dosya adına göre değil. Önemli olan ingest sırasının tekrarlanabilirliği.
    yollar = [
        str(p.relative_to(tmp_path)).replace("\\", "/")
        for p in chunking.iter_corpus_files(tmp_path)
    ]
    assert yollar == ["a.md", "alt/d.md", "b.txt"]


def test_kaynak_adi_corpus_koke_gore_goreli(tmp_path):
    (tmp_path / "alt").mkdir()
    hedef = tmp_path / "alt" / "notlar.md"
    hedef.write_text("İçerik burada.", encoding="utf-8")

    source, chunks = chunking.chunk_file(hedef, tmp_path)
    assert source == "alt/notlar.md"
    assert chunks == ["İçerik burada."]
