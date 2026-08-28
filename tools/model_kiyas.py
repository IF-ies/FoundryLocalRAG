"""Sohbet modellerini AYNI sorularla kıyasla ve sonucu ölçerek yaz.

Model seçimi tahminle değil ölçümle yapılsın diye var. Kullanım:

    python tools/model_kiyas.py phi-3.5-mini qwen3-4b qwen2.5-7b

Her model için indirme + yükleme yapılır (ilk seferde yavaş), sonra aynı
sorular sorulur. Çıktı elle okunmak içindir: Türkçe akıcılığı, bağlama
sadakati ve "bilmiyorum" davranışı gözle değerlendirilir.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from foundry_rag import config  # noqa: E402

BAGLAM = """[1] Kaynak: sirket.md (parça 0)
Zerdali Makina 2019 yılında Kayseri'de kuruldu. Kurucusu Nuray Akbulut'tur.
Fabrika üç vardiya çalışır. Vardiya değişimi saat 08:00, 16:00 ve 24:00'te olur."""

SORULAR = [
    # (etiket, soru, bağlam)
    ("tr-genel", "Türkiye'nin başkenti neresidir? Tek kelimeyle cevapla.", None),
    ("tr-baglam", "Zerdali Makina'yı kim kurdu?", BAGLAM),
    ("tr-bilmiyorum", "Zerdali Makina'nın 2024 cirosu ne kadardı?", BAGLAM),
]


def mesajlar(soru: str, baglam: str | None) -> list[dict[str, str]]:
    if baglam is None:
        return [{"role": "user", "content": soru}]
    from foundry_rag.rag import SYSTEM_PROMPT

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"BAĞLAM:\n{baglam}\n\nSORU: {soru}"},
    ]


def dene(alias: str) -> None:
    from foundry_rag.client import _ensure_execution_providers, _manager

    print(f"\n{'=' * 70}\nMODEL: {alias}\n{'=' * 70}", flush=True)
    manager = _manager()
    _ensure_execution_providers(manager, lambda m: print(m, flush=True))

    model = manager.catalog.get_model(alias)
    if model is None:
        print(f"  BULUNAMADI (foundry model list ile kontrol et)", flush=True)
        return

    print(f"  varyant: {model.id}", flush=True)
    if not model.is_cached:
        print("  indiriliyor...", flush=True)
        son = -20.0

        def ilerleme(y: float) -> None:
            nonlocal son
            if y - son >= 20.0 or y >= 100.0:
                son = y
                print(f"    %{y:.0f}", flush=True)

        model.download(progress_callback=ilerleme)
    if not model.is_loaded:
        model.load()

    istemci = model.get_chat_client()
    istemci.settings.temperature = config.CHAT_TEMPERATURE
    istemci.settings.max_tokens = config.CHAT_MAX_TOKENS

    for etiket, soru, baglam in SORULAR:
        t = time.perf_counter()
        try:
            yanit = istemci.complete_chat(mesajlar(soru, baglam))
            metin = (yanit.choices[0].message.content or "").strip()
        except Exception as exc:
            metin = f"HATA: {exc}"
        gecen = time.perf_counter() - t
        # Uzun cevapları kırp; amaç kaliteyi görmek, tam metni değil.
        kisa = metin if len(metin) <= 400 else metin[:400] + " ...[kırpıldı]"
        print(f"\n  [{etiket}] ({gecen:.1f} sn)\n  {kisa}", flush=True)

    model.unload()


if __name__ == "__main__":
    adaylar = sys.argv[1:] or ["phi-3.5-mini", "qwen3-4b"]
    for ad in adaylar:
        dene(ad)
