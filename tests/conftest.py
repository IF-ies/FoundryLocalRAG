"""Ortak test yardımcıları.

Buradaki sahte istemci KASITLI olarak aptaldır: gerçek embedding üretmez,
kelime örtüşmesine bakar. Amaç retrieval/prompt mantığını model olmadan
sınamak. Model gerektiren gerçek testler `-m model` ile ayrı çalışır.
"""

from __future__ import annotations

import pytest

from foundry_rag import db


@pytest.fixture
def conn():
    connection = db.connect(":memory:")
    yield connection
    connection.close()


class FakeClient:
    """Sabit sözlüğe göre vektör üreten sahte model.

    Her kelime bir boyuta karşılık gelir; metin o kelimeyi içeriyorsa 1, yoksa 0.
    Böylece benzerlik değerleri elde hesaplanabilir olur.
    """

    def __init__(self, vocabulary: list[str], chat_reply: str = "sahte cevap"):
        self.vocabulary = vocabulary
        self.chat_reply = chat_reply
        self.last_messages: list[dict[str, str]] | None = None
        self.chat_calls = 0

    def embed(self, texts):
        return [self.embed_one(t) for t in texts]

    def embed_one(self, text: str):
        lowered = text.lower()
        return [1.0 if word in lowered else 0.0 for word in self.vocabulary]

    def chat(self, messages):
        self.last_messages = messages
        self.chat_calls += 1
        return self.chat_reply
