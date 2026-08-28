"""Tek yerden ayarlar. Ortam değişkeniyle ezilebilir, kod değiştirmeye gerek yok."""

from __future__ import annotations

import os
from pathlib import Path

# Foundry Local SDK bu adla kendi veri/gunluk klasorunu ayirir.
APP_NAME = "FoundryLocalRAG"

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORPUS_DIR = Path(os.environ.get("FOUNDRY_RAG_CORPUS", PROJECT_ROOT / "corpus"))
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = Path(os.environ.get("FOUNDRY_RAG_DB", DATA_DIR / "rag.db"))

# Model takma adları (alias). Foundry Local donanıma uygun varyantı kendisi seçer:
# CUDA varsa GPU, yoksa CPU. Gerçek model kimliği çalışma anında SDK'dan okunur.
CHAT_MODEL_ALIAS = os.environ.get("FOUNDRY_RAG_CHAT_MODEL", "phi-3.5-mini")
EMBED_MODEL_ALIAS = os.environ.get("FOUNDRY_RAG_EMBED_MODEL", "qwen3-embedding-0.6b")

# Chunk'lama: paragraf sınırlarında böl, bu üst sınırı aşma.
CHUNK_MAX_CHARS = 1200
# Ardışık chunk'lar arasında taşınan bağlam (cümle ortasında kopan bilgi için).
CHUNK_OVERLAP_CHARS = 150

# Retrieval
TOP_K = 3
# Bu benzerliğin altındaki hiçbir chunk bağlama girmez -> model "bilmiyorum" der.
# DİKKAT: bu değer TAHMİN DEĞİL, Faz 7'de gerçek sorularla ölçülüp güncellenir.
MIN_SIMILARITY = 0.30

# Üretim ayarları — RAG'de yaratıcılık istemiyoruz.
CHAT_TEMPERATURE = 0.2
CHAT_MAX_TOKENS = 800

# Bağlamda cevap yoksa modelin vermesi gereken tam karşılık.
# Testler bu ifadeyi arar; değiştirirsen testler de değişir.
UNKNOWN_ANSWER = "Bu soruyu verilen belgelerle cevaplayamıyorum."
