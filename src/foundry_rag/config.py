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
# ÖLÇÜLDÜ (tools/model_kiyas.py, 28 Ağu 2026) — altı aday denendi, kazanan
# ministral-3-3b: Türkçesi temiz, uydurmuyor, 3.6 GB. Elenenler:
#   qwen2.5-7b  : doğru ama yavaş (RAG'de 8-11 sn) ve 5.5 GB
#   phi-3.5-mini: dilbilgisi bozuk, 'bilmiyorum' ifadesini değiştiriyor
#   qwen3-4b    : cevabın içine <think> bloğu sızdırıyor
#   qwen2.5-1.5b: TEHLİKELİ — 'cevaplayamıyorum' dedikten sonra rakam uyduruyor
#   qwen3.5-2b  : Türkçe bozuk ('Zrdali', 'BuBelgeleCevaplayamıyorum')
# CUDA varsa GPU, yoksa CPU. Gerçek model kimliği çalışma anında SDK'dan okunur.
CHAT_MODEL_ALIAS = os.environ.get("FOUNDRY_RAG_CHAT_MODEL", "ministral-3-3b-instruct-2512")
EMBED_MODEL_ALIAS = os.environ.get("FOUNDRY_RAG_EMBED_MODEL", "qwen3-embedding-0.6b")

# Chunk'lama: paragraf sınırlarında böl, bu üst sınırı aşma.
# ÖLÇÜLDÜ (tools/degerlendirme.py, 11 soruluk set): 1200 -> 7/11, 500 -> 8/11,
# 300 -> 10/11. Tek chunk'a çok konu sığdırınca embedding bulanıklaşıyor ve
# içindeki ayrıntı sorguya yakın çıkmıyor. Küçük chunk hem daha doğru hem hızlı.
CHUNK_MAX_CHARS = int(os.environ.get("FOUNDRY_RAG_CHUNK_CHARS", "300"))
# Ardışık chunk'lar arasında taşınan bağlam (cümle ortasında kopan bilgi için).
CHUNK_OVERLAP_CHARS = int(os.environ.get("FOUNDRY_RAG_CHUNK_OVERLAP", "100"))

# Retrieval
# TOP_K=5 iki kez denendi, doğruluğa hiçbir katkısı olmadı ama süreyi
# 1.9 -> 2.5 sn'ye çıkardı. 3'te kalıyor.
TOP_K = int(os.environ.get("FOUNDRY_RAG_TOP_K", "3"))
# Bu benzerliğin altındaki hiçbir chunk bağlama girmez -> model "bilmiyorum" der.
# ÖLÇÜLDÜ (gerçek corpus, 28 Ağu 2026): konuyla ilgili parçalar 0.39-0.57
# aralığında, alakasız sorularda en iyi parça 0.30-0.31'de kalıyor.
# 0.35 bu iki kümeyi ayırıyor. Corpus değişirse bu değer YENİDEN ölçülmeli.
MIN_SIMILARITY = 0.35

# Üretim ayarları — RAG'de yaratıcılık istemiyoruz.
CHAT_TEMPERATURE = 0.2
CHAT_MAX_TOKENS = 800

# Bağlamda cevap yoksa modelin vermesi gereken karşılık.
UNKNOWN_ANSWER = "Bu soruyu verilen belgelerle cevaplayamıyorum."

# Tespit BİREBİR eşitlikle yapılmaz: modeller ifadeyi kendilerince yeniden
# yazıyor (ölçüldü — phi-3.5-mini "...cevaplamadım." dedi). Birebir arama
# yapsaydık model doğru davrandığı hâlde "cevap uydurdu" sanırdık.
# Bu yüzden ifadenin değişmeyen çekirdeği aranır.
UNKNOWN_MARKER = "belgelerle cevapla"
