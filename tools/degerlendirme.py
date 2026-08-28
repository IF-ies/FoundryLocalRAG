"""Corpus üzerinde cevap DOĞRULUĞUNU ölçer.

"bilmiyorum dedi mi" yetmez — yanlış belgeden uydurulmuş bir cevap da
"bilmiyorum değil" olduğu için doğru sanılır. Bu yüzden her cevaplanabilir
soru için cevapta geçmesi GEREKEN anahtarlar da kontrol edilir.

Sorular TÜRKÇE, belgeler İNGİLİZCE — bu kasıtlı: gerçek kullanım böyle olacak.
Anahtarlar bu yüzden "|" ile hem Türkçe hem İngilizce karşılık içerir ve
Türkçe ekleri yakalasın diye köke yazılır ("çekirdeğini" -> "çekirde").

Kullanım:
    python tools/degerlendirme.py
    FOUNDRY_RAG_CHUNK_CHARS=500 python tools/degerlendirme.py   (kıyas için)

Not: chunk ayarı değiştiyse ÖNCE `python main.py ingest --reset` çalıştır.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from foundry_rag import config, db, rag  # noqa: E402

# (soru, cevapta geçmesi gereken anahtarlar | None = "bilmiyorum" beklenir)
# Her anahtar için "|" ile ayrılan alternatiflerden BİRİ yeterlidir.
SORULAR: list[tuple[str, list[str] | None]] = [
    # --- 01: bilinç iddia eden modeller ---
    ("Bilinçli olduğunu iddia edecek şekilde ince ayar yapılan model hangisidir?", ["gpt-4.1"]),
    (
        "İnce ayarlı model, kendi akıl yürütmesinin izlenmesine nasıl bakıyor?",
        ["olumsuz|negatif|hoşlanm|istemi|karşı|rahatsız"],
    ),
    # --- 02: ahlaki statü, ilişkisel çerçeve ---
    (
        "Relate çerçevesi hangi gerçek vakalar üzerinden temellendiriliyor?",
        ["lamda", "replika|replika|replika", "character"],
    ),
    # --- 03: yapay kişiler ---
    (
        "Rawls'un siyasal kişi kavramındaki iki ahlaki güç nedir?",
        ["adalet|justice", "iyi|good"],
    ),
    (
        "Yapay bir sistemin kişi sayılması için duyarlılık (sentience) şart mıdır?",
        ["gerektirmez|gerekmez|şart değil|zorunlu değil|hayır|değildir|olmadan"],
    ),
    # --- 04: kimin değerleri ---
    (
        "Yanlış hizalanma hangi üç eksende çözümleniyor?",
        ["amaç|hedef|objective", "bilgi|information", "asil|principal|vekil"],
    ),
    (
        "Değer uyumu sorunu temelde mühendislik sorunu mudur yoksa yönetişim sorunu mudur?",
        ["yönetişim|governance|yönetim"],
    ),
    # --- 05: AGI tanımlanabilir ---
    (
        "AGI hangi ölçüte göre tanımlanıyor?",
        ["yetişkin|adult"],
    ),
    (
        "AGI tanımı hangi psikometri kuramına dayandırılıyor?",
        ["cattell"],
    ),
    # --- 06: AGI söylemi eleştirisi (05 ile çelişir) ---
    (
        "AGI tanımlarının değer yüklü olduğunu savunan eleştiri ne diyor?",
        ["değer|value|varsayım|assumption|siyas|politik|political"],
    ),
    # --- hiçbir belgede olmayanlar ---
    ("Bu makalelerin toplam atıf sayısı kaçtır?", None),
    ("Türkiye'de yapay zekâ yasası hangi tarihte yürürlüğe girdi?", None),
    ("Yazarların çalıştığı kurumlardaki maaş ortalaması nedir?", None),
]


def main() -> int:
    from foundry_rag.client import FoundryClient

    conn = db.connect()
    toplam_chunk = db.count(conn)
    if toplam_chunk == 0:
        print("Veritabanı boş. Önce: python main.py ingest")
        return 1

    print(f"chunk boyutu : {config.CHUNK_MAX_CHARS} / overlap {config.CHUNK_OVERLAP_CHARS}")
    print(f"veritabanı   : {toplam_chunk} chunk")
    print(f"eşik         : {config.MIN_SIMILARITY}")
    print(f"top_k        : {config.TOP_K}\n")

    client = FoundryClient()
    gecen = 0
    sureler: list[float] = []

    for soru, anahtarlar in SORULAR:
        cevap = rag.answer_query(client, conn, soru)
        sureler.append(cevap.elapsed_seconds)

        if anahtarlar is None:
            ok = cevap.is_unknown
            sebep = "" if ok else "belgede olmayan soruya cevap üretildi"
        elif cevap.is_unknown:
            ok = False
            sebep = "belgede bilgi VAR ama 'bilmiyorum' dendi"
        else:
            metin = cevap.text.casefold()
            eksik = [
                a
                for a in anahtarlar
                if not any(sec.casefold() in metin for sec in a.split("|"))
            ]
            ok = not eksik
            sebep = "" if ok else f"cevapta eksik: {eksik}"

        gecen += ok
        print(f"{'GECTI' if ok else 'KALDI'}  {soru}")
        ilk_satir = next((s for s in cevap.text.splitlines() if s.strip()), "")
        print(f"       ({cevap.elapsed_seconds:.1f} sn) {ilk_satir[:110]}")
        if not ok:
            print(f"       -> {sebep}")
            if cevap.hits:
                print("       -> getirilen: " + ", ".join(
                    f"{h.chunk.source}#{h.chunk.chunk_index}({h.score:.2f})" for h in cevap.hits
                ))
        print()

    ortalama = sum(sureler) / len(sureler)
    print("=" * 72)
    print(f"SONUC: {gecen}/{len(SORULAR)} — ortalama {ortalama:.1f} sn")
    return 0 if gecen == len(SORULAR) else 1


if __name__ == "__main__":
    raise SystemExit(main())
