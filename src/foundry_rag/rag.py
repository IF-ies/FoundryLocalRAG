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
2. BAĞLAM soruyu cevaplamaya yetmiyorsa tam olarak şunu yaz: "{config.UNKNOWN_ANSWER}"
   Ardından istersen tek cümleyle neyin eksik olduğunu belirt. Uydurma yapma.
3. Cevabın sonunda kullandığın kaynakları "Kaynaklar:" başlığı altında listele.
4. Soru hangi dilde sorulduysa o dilde cevap ver.
5. Kısa ve doğrudan yaz."""


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
        return config.UNKNOWN_ANSWER in self.text


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
    return Answer(question, text, hits, time.perf_counter() - started)
