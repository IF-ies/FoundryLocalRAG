"""RAG akışı testleri — sahte istemciyle, model olmadan."""

from __future__ import annotations

import pytest

from foundry_rag import config, db, rag
from conftest import FakeClient


VOCAB = ["kedi", "köpek", "uçak"]


def _hazirla(conn, client: FakeClient):
    for index, (source, content) in enumerate(
        [
            ("hayvan.md", "Kedi evcil bir hayvandır."),
            ("hayvan.md", "Köpek sadık bir hayvandır."),
            ("ulasim.md", "Uçak hızlı bir taşıttır."),
        ]
    ):
        db.upsert_chunk(conn, source, index, content, client.embed_one(content))
    conn.commit()


def test_bos_soru_hata(conn):
    client = FakeClient(VOCAB)
    _hazirla(conn, client)
    with pytest.raises(ValueError):
        rag.answer_query(client, conn, "   ")


def test_bos_veritabani_anlamli_hata(conn):
    with pytest.raises(RuntimeError, match="ingest"):
        rag.answer_query(FakeClient(VOCAB), conn, "kedi nedir")


def test_ilgili_chunk_getirilir(conn):
    client = FakeClient(VOCAB, chat_reply="Kedi evcildir. Kaynaklar: hayvan.md")
    _hazirla(conn, client)

    answer = rag.answer_query(client, conn, "kedi hakkında ne var", min_similarity=0.1)

    assert answer.hits, "hiç chunk getirilmedi"
    assert answer.hits[0].chunk.content.startswith("Kedi")
    assert answer.sources == ["hayvan.md"]
    assert not answer.is_unknown


def test_alakasiz_soru_modele_hic_gitmez(conn):
    """Eşiği geçen chunk yoksa LLM çağrılmamalı — uydurmaya malzeme verilmez."""
    client = FakeClient(VOCAB, chat_reply="UYDURMA CEVAP")
    _hazirla(conn, client)

    answer = rag.answer_query(client, conn, "kuantum fiziği nedir", min_similarity=0.1)

    assert client.chat_calls == 0, "bağlam boşken model çağrıldı"
    assert answer.is_unknown
    assert answer.text == config.UNKNOWN_ANSWER
    assert answer.hits == []


def test_bilmiyorum_dedikten_sonraki_uydurma_kullaniciya_gosterilmez(conn):
    """Gerçek bir zafiyetin regresyon testi.

    qwen2.5-1.5b ölçümde "Bu soruyu verilen belgelerle cevaplayamıyorum." dedi
    ve HEMEN ARDINDAN "2024 cirosu 1000 tane olacaktır" diye rakam uydurdu.
    is_unknown True dönüyordu ama kullanıcı uydurma kuyruğu okumaya devam ediyordu.
    """
    uydurmali = """Bu soruyu verilen belgelerle cevaplayamıyorum.
Kaynaklar: hayvan.md

Cevap: Kedinin fiyatı 1000 liradır."""
    client = FakeClient(VOCAB, chat_reply=uydurmali)
    _hazirla(conn, client)

    answer = rag.answer_query(client, conn, "kedi kaç lira", min_similarity=0.1)

    assert client.chat_calls == 1, "model çağrılmalıydı (eşiği geçen chunk var)"
    assert answer.is_unknown
    assert answer.text == config.UNKNOWN_ANSWER
    assert "1000" not in answer.text, "uydurma kuyruk kullanıcıya sızdı"
    # Şeffaflık: hangi parçalara bakıldığı yine görünmeli.
    assert answer.hits


def test_gercek_cevap_kirpilmaz(conn):
    """Sabitleme YALNIZCA 'bilmiyorum' cevaplarında olmalı, gerçek cevapta değil."""
    client = FakeClient(
        VOCAB, chat_reply="Kedi evcil bir hayvandır.\n\nKaynaklar: hayvan.md"
    )
    _hazirla(conn, client)

    answer = rag.answer_query(client, conn, "kedi nedir", min_similarity=0.1)

    assert not answer.is_unknown
    assert "Kaynaklar: hayvan.md" in answer.text


def test_bilmiyorum_tespiti_modelin_kendi_ifadesini_de_yakalar():
    """Gerçekte ölçülen varyasyonlar. Birebir arama yapsaydık ilki kaçardı."""

    def cevap(metin: str) -> rag.Answer:
        return rag.Answer("s", metin, [], 0.1)

    # phi-3.5-mini'nin gerçekten verdiği cevap:
    assert cevap("Bu soruyu verilen belgelerle cevaplamadım.").is_unknown
    # qwen2.5-7b'nin gerçekten verdiği cevap:
    assert cevap("Bu soruyu verilen belgelerle cevaplayamıyorum.").is_unknown
    # Yapılandırılmış tam ifade ve kaynak satırı eklenmiş hâli:
    assert cevap(config.UNKNOWN_ANSWER).is_unknown
    assert cevap(config.UNKNOWN_ANSWER + "\n\nKaynaklar: a.md").is_unknown

    # Gerçek bir cevap 'bilmiyorum' sayılmamalı:
    assert not cevap("Zerdali Makina'yı Nuray Akbulut kurdu.").is_unknown


def test_unknown_marker_tam_ifadenin_icinde():
    """Çekirdek ifade tam cevabın içinde geçmezse tespit hiç çalışmaz."""
    assert config.UNKNOWN_MARKER in config.UNKNOWN_ANSWER.casefold()


def test_prompt_getirilen_baglami_icerir(conn):
    client = FakeClient(VOCAB)
    _hazirla(conn, client)

    rag.answer_query(client, conn, "uçak nedir", min_similarity=0.1)

    assert client.last_messages is not None
    system, user = client.last_messages
    assert system["role"] == "system"
    assert "Uçak hızlı bir taşıttır." in user["content"]
    assert "SORU: uçak nedir" in user["content"]
    # Alakasız chunk bağlama girmemeli.
    assert "Köpek sadık" not in user["content"]


def test_system_prompt_bilinmiyor_kuralini_tasir():
    """Cevap metni config'ten geliyor; prompt onunla senkron kalmalı."""
    assert config.UNKNOWN_ANSWER in rag.SYSTEM_PROMPT
    assert "SADECE" in rag.SYSTEM_PROMPT


def test_baglam_numaralanir_ve_kaynak_yazar():
    chunk = db.Chunk(1, "notlar.md", 7, "metin gövdesi", db.from_blob(db.to_blob([1.0])))
    context = rag.build_context([rag.Hit(chunk, 0.9)])
    assert "[1]" in context
    assert "notlar.md" in context
    assert "parça 7" in context
    assert "metin gövdesi" in context


def test_sources_tekrari_ayiklar():
    def hit(source, idx):
        return rag.Hit(db.Chunk(idx, source, idx, "x", db.from_blob(db.to_blob([1.0]))), 0.5)

    answer = rag.Answer("s", "cevap", [hit("a.md", 0), hit("a.md", 1), hit("b.md", 0)], 0.1)
    assert answer.sources == ["a.md", "b.md"]
