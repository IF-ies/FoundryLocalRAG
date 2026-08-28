"""RAG çekirdeği: Retrieve -> Augment -> Generate.

Prompt kurgusu ayrı fonksiyonlarda tutuluyor ki model çağırmadan test edilebilsin.
"""

from __future__ import annotations

import sqlite3
import time
from typing import NamedTuple, Protocol, Sequence

from . import config, db
from .retrieval import Hit, rank

SYSTEM_PROMPT = f"""Sen bir belge asistanısın. SADECE sana verilen BAĞLAM bölümündeki bilgiyi kullan.

Kurallar:
1. Cevabı yalnızca BAĞLAM'dan üret. Genel bilgine, tahminine veya varsayımına ASLA başvurma.
2. BAĞLAM soruyu KISMEN cevaplıyorsa, cevaplayabildiğin kadarını ver ve neyin
   eksik kaldığını tek cümleyle belirt. Kısmi bilgi varken "cevaplayamıyorum" deme.
3. BAĞLAM'da soruyla ilgili HİÇBİR bilgi yoksa tam olarak şunu yaz:
   "{config.UNKNOWN_ANSWER}" — ve başka hiçbir şey ekleme, tahmin yürütme.
4. Cevabın sonunda kullandığın kaynakları "Kaynaklar:" başlığı altında listele.
   Kaynak olarak YALNIZCA BAĞLAM'da yazan dosya adlarını yaz. Bağlantı, URL veya
   sayfa adresi UYDURMA — bağlamda yoksa yazma.
5. Soru hangi dilde sorulduysa o dilde cevap ver.
6. Kısa ve doğrudan yaz."""


class Embedder(Protocol):
    """rag katmanının modelden tek beklentisi. Testte sahte nesneyle değiştirilebilir."""

    def embed_one(self, text: str) -> list[float]: ...

    def chat(self, messages: list[dict[str, str]]) -> str: ...


class Answer(NamedTuple):
    question: str
    text: str
    hits: list[Hit]
    elapsed_seconds: float

    @property
    def sources(self) -> list[str]:
        seen: list[str] = []
        for hit in self.hits:
            if hit.chunk.source not in seen:
                seen.append(hit.chunk.source)
        return seen

    @property
    def is_unknown(self) -> bool:
        """Model 'bu belgelerle cevaplayamam' demiş mi?

        Birebir değil, ifadenin çekirdeğine bakılır — modeller cümleyi
        kendilerince kuruyor (bkz. config.UNKNOWN_MARKER).
        """
        return config.UNKNOWN_MARKER in self.text.casefold()


def build_context(hits: Sequence[Hit]) -> str:
    """Getirilen chunk'ları numaralı, kaynağı belli bir bağlam metnine çevir."""
    blocks = []
    for index, hit in enumerate(hits, start=1):
        blocks.append(
            f"[{index}] Kaynak: {hit.chunk.source} (parça {hit.chunk.chunk_index})\n{hit.chunk.content}"
        )
    return "\n\n---\n\n".join(blocks)


def build_messages(question: str, hits: Sequence[Hit]) -> list[dict[str, str]]:
    context = build_context(hits) if hits else "(bağlam bulunamadı)"
    user = f"BAĞLAM:\n{context}\n\nSORU: {question}"
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]


def answer_query(
    client: Embedder,
    conn: sqlite3.Connection,
    question: str,
    top_k: int | None = None,
    min_similarity: float | None = None,
) -> Answer:
    """Soruyu cevapla. Bağlam boşsa modele hiç gitmeden 'bilmiyorum' döner."""
    started = time.perf_counter()
    question = question.strip()
    if not question:
        raise ValueError("Soru boş olamaz")

    chunks = db.all_chunks(conn)
    if not chunks:
        raise RuntimeError(
            "Veritabanı boş. Önce belgeleri yükle: python main.py ingest"
        )

    query_vector = client.embed_one(question)
    hits = rank(query_vector, chunks, top_k=top_k, min_similarity=min_similarity)

    if not hits:
        # Eşiği geçen chunk yok — model çağırmak hem gereksiz hem de uydurma riski.
        return Answer(question, config.UNKNOWN_ANSWER, [], time.perf_counter() - started)

    text = client.chat(build_messages(question, hits))
    cevap = Answer(question, text, hits, time.perf_counter() - started)

    if cevap.is_unknown:
        # Model "cevaplayamam" dedikten SONRA uydurma eklemeye devam edebiliyor
        # (ölçüldü: qwen2.5-1.5b "...cevaplayamıyorum." dedi, hemen ardından
        # "2024 cirosu 1000 tane olacaktır" diye rakam uydurdu). Kullanıcı o
        # kuyruğu okuyup gerçek sanabilir; bu yüzden cevabı sabit ifadeye
        # indiriyoruz. Getirilen parçalar yine gösterilir, şeffaflık korunur.
        return Answer(question, config.UNKNOWN_ANSWER, hits, cevap.elapsed_seconds)

    return cevap
