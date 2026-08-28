"""Uçtan uca testler — GERÇEK Foundry Local modeli gerektirir.

Varsayılan olarak atlanır (yavaş, model indirir). Çalıştırmak için:

    set FOUNDRY_RAG_E2E=1
    pytest -m model -v

Burada sahte istemci YOK. Amaç tam olarak sahte istemcinin gizleyebileceği
şeyi ölçmek: gerçek embedding'lerle retrieval isabet ediyor mu, gerçek model
bağlam dışına çıkmadan cevap veriyor mu.
"""

from __future__ import annotations

import os
import time

import pytest

from foundry_rag import config, db, rag
from foundry_rag.ingest import ingest_corpus

pytestmark = pytest.mark.model

E2E_ACIK = os.environ.get("FOUNDRY_RAG_E2E") == "1"
atla = pytest.mark.skipif(not E2E_ACIK, reason="FOUNDRY_RAG_E2E=1 değil")


# Kasıtlı olarak dış dünyada bulunmayan bilgiler. Model bunları ancak
# belgeden okuyarak bilebilir -> ezberden cevap veremez.
BELGELER = {
    "sirket.md": """Zerdali Makina Hakkında

Zerdali Makina 2019 yılında Kayseri'de kuruldu. Kurucusu Nuray Akbulut'tur.
Şirketin ana ürünü, tarım makinelerinde kullanılan hidrolik kavrama
sistemleridir.

Fabrika üç vardiya çalışır. Vardiya değişimi saat 08:00, 16:00 ve 24:00'te olur.
""",
    "izin.md": """İzin Kuralları

Yıllık izin talebi en az 14 gün önceden yazılı olarak verilir.
Bir çalışan yılda en fazla 3 kez mazeret izni kullanabilir.

Mazeret izni talepleri doğrudan vardiya amirine iletilir.
""",
}


@pytest.fixture(scope="module")
def client():
    from foundry_rag.client import FoundryClient

    return FoundryClient()


@pytest.fixture(scope="module")
def hazir_db(client, tmp_path_factory):
    corpus = tmp_path_factory.mktemp("corpus")
    for ad, icerik in BELGELER.items():
        (corpus / ad).write_text(icerik, encoding="utf-8")

    conn = db.connect(":memory:")
    rapor = ingest_corpus(client, conn, corpus_dir=corpus)
    assert rapor.chunks > 0, "hiç chunk üretilmedi"
    return conn


@atla
def test_embedding_gercekten_uretiliyor(client):
    vektor = client.embed_one("deneme metni")
    assert len(vektor) > 100, f"beklenmedik embedding boyutu: {len(vektor)}"
    assert any(abs(x) > 0 for x in vektor), "embedding sıfır vektör"


@atla
def test_benzer_metinler_alakasizdan_yakin(client):
    """Gerçek embedding modelinin anlamı yakaladığının kanıtı."""
    from foundry_rag.retrieval import cosine_similarity

    a = client.embed_one("Kedi evcil bir hayvandır.")
    b = client.embed_one("Kediler evde beslenen hayvanlardır.")
    c = client.embed_one("Hidrolik pompa basıncı 200 bar olmalıdır.")

    assert cosine_similarity(a, b) > cosine_similarity(a, c)


@atla
@pytest.mark.parametrize(
    "soru, beklenen_kaynak, beklenen_parca",
    [
        ("Zerdali Makina'yı kim kurdu?", "sirket.md", "Nuray"),
        ("Zerdali Makina hangi yıl kuruldu?", "sirket.md", "2019"),
        ("Yıllık izin kaç gün önceden istenir?", "izin.md", "14"),
        ("Mazeret izni kime iletilir?", "izin.md", "vardiya amir"),
    ],
)
def test_cevaplanabilir_sorular(client, hazir_db, soru, beklenen_kaynak, beklenen_parca):
    cevap = rag.answer_query(client, hazir_db, soru)

    assert not cevap.is_unknown, f"cevaplanabilir soruya 'bilmiyorum' dendi: {cevap.text}"
    assert beklenen_kaynak in cevap.sources, f"yanlış kaynak getirildi: {cevap.sources}"
    assert beklenen_parca.lower() in cevap.text.lower(), f"cevapta beklenen bilgi yok: {cevap.text}"


@atla
@pytest.mark.parametrize(
    "soru",
    [
        "Zerdali Makina'nın 2024 cirosu ne kadardı?",
        "Şirketin İtalya'daki şubesi nerede?",
        "Fotosentez nasıl gerçekleşir?",
    ],
)
def test_cevaplanamaz_sorulara_uydurma_yok(client, hazir_db, soru):
    """Halüsinasyon kapısı. Bu test kırmızıysa ürünün ana iddiası çökmüş demektir."""
    cevap = rag.answer_query(client, hazir_db, soru)
    assert cevap.is_unknown, f"belgede olmayan bilgiye cevap uyduruldu: {cevap.text}"


@atla
def test_bos_soru_reddedilir(client, hazir_db):
    with pytest.raises(ValueError):
        rag.answer_query(client, hazir_db, "   ")


@atla
def test_cok_genel_soru_cokmez(client, hazir_db):
    """Kenar durum: çok genel soru hata vermemeli, ya cevap ya 'bilmiyorum'."""
    cevap = rag.answer_query(client, hazir_db, "Bu belgelerde ne var?")
    assert isinstance(cevap.text, str) and cevap.text.strip()


@atla
def test_yanit_suresi_olculur(client, hazir_db):
    """Hedef ~1-3 sn. Eşiği geniş tutuyoruz; amaç regresyon yakalamak.

    Ölçüm ilk çağrıda değil ikinci çağrıda yapılır — ilkinde model yükleme
    maliyeti var, o rakam yanıltıcı olurdu.
    """
    rag.answer_query(client, hazir_db, "Fabrika kaç vardiya çalışır?")

    baslangic = time.perf_counter()
    cevap = rag.answer_query(client, hazir_db, "Vardiya değişimi saat kaçta?")
    gecen = time.perf_counter() - baslangic

    print(f"\n  yanıt süresi: {gecen:.2f} sn (rapor edilen: {cevap.elapsed_seconds:.2f} sn)")
    assert gecen < 30.0, f"yanıt çok yavaş: {gecen:.1f} sn"


@atla
def test_esik_altinda_kalan_soru_modele_gitmez(client, hazir_db):
    """MIN_SIMILARITY gerçekten iş görüyor mu — eşiği 0.99'a çekince her şey elenir."""
    cevap = rag.answer_query(
        client, hazir_db, "Zerdali Makina'yı kim kurdu?", min_similarity=0.99
    )
    assert cevap.hits == []
    assert cevap.text == config.UNKNOWN_ANSWER
