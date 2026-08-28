"""Vektör arama: brute-force cosine similarity.

Küçük N (birkaç bin chunk) için yeterli ve bağımlılıksız. Ölçeklenince
Seviye 2'de gerçek bir vektör indeksine (sqlite-vec / Qdrant) geçilecek.
"""

from __future__ import annotations

from typing import NamedTuple, Sequence

import numpy as np

from . import config
from .db import Chunk


class Hit(NamedTuple):
    chunk: Chunk
    score: float


def cosine_similarity(a: Sequence[float] | np.ndarray, b: Sequence[float] | np.ndarray) -> float:
    """İki vektör arasındaki kosinüs benzerliği. Sıfır vektör için 0.0."""
    va = np.asarray(a, dtype=np.float64)
    vb = np.asarray(b, dtype=np.float64)
    if va.shape != vb.shape:
        raise ValueError(f"Vektör boyutları uyuşmuyor: {va.shape} vs {vb.shape}")
    norm = np.linalg.norm(va) * np.linalg.norm(vb)
    if norm == 0.0:
        return 0.0
    return float(np.dot(va, vb) / norm)


def rank(
    query_embedding: Sequence[float] | np.ndarray,
    chunks: Sequence[Chunk],
    top_k: int | None = None,
    min_similarity: float | None = None,
) -> list[Hit]:
    """Chunk'ları sorguya yakınlığa göre sırala, eşiğin altındakileri ele.

    Eşik altındaki her şeyi atmak bilinçli: bağlam boş dönerse cevap üretici
    'bilmiyorum' demek zorunda kalır, uydurmaya malzeme bulamaz.
    """
    k = top_k if top_k is not None else config.TOP_K
    threshold = min_similarity if min_similarity is not None else config.MIN_SIMILARITY

    scored = [Hit(chunk, cosine_similarity(query_embedding, chunk.embedding)) for chunk in chunks]
    scored.sort(key=lambda hit: hit.score, reverse=True)
    return [hit for hit in scored[:k] if hit.score >= threshold]
