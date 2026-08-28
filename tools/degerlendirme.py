"""Corpus üzerinde cevap DOĞRULUĞUNU ölçer.

"bilmiyorum dedi mi" yetmez — yanlış belgeden uydurulmuş bir cevap da
"bilmiyorum değil" olduğu için doğru sanılır. Bu yüzden her cevaplanabilir
soru için cevapta geçmesi GEREKEN anahtarlar da kontrol edilir.

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
SORULAR: list[tuple[str, list[str] | None]] = [
    # --- ders notu (dışarıda bulunamayacak bilgiler) ---
    ("Bulut Bilişim final sınavı ne zaman ve hangi derslikte yapılacak?", ["14 Ocak 2027", "B-204"]),
    ("Dönem projesi en geç ne zaman teslim edilir?", ["7 Ocak 2027"]),
    ("Geç teslimde günlük kaç puan kırılıyor?", ["10"]),
    # "|" ile ayrılan alternatiflerden BİRİ yeterli — model aynı bilgiyi
    # farklı kelimelerle ifade edebiliyor ("yasak" / "kullanılamaz").
    ("Sınavda basılı kaynak kullanılabilir mi?", ["yasak|kullanılamaz|kullanılmaz|izin veril"]),
    # Anahtar kelimeler Türkçe EK almış hâlleri de yakalayacak şekilde köke
    # yazılır ("çekirdeğini" -> "çekirde"); yoksa doğru cevap yanlış sayılır.
    ("Konteyner ile sanal makine arasındaki temel fark nedir?", ["çekirde"]),
    ("Tip-1 hipervizör nedir?", ["donanım"]),
    # --- proje dokümanları ---
    ("FoundryLocalRAG projesinde hangi embedding modeli kullanılıyor?", ["qwen3-embedding"]),
    ("Benzerlik eşiği (MIN_SIMILARITY) kaça ayarlandı?", ["0.35"]),
    # --- hiçbir belgede olmayanlar ---
    ("Bu dersin vize sınavı ne zaman yapılmıştı?", None),
    ("Bulut Bilişim dersinin hocası kimdir?", None),
    ("Bu projenin bütçesi kaç lira?", None),
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
    print(f"eşik         : {config.MIN_SIMILARITY}\n")

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
        print(f"       ({cevap.elapsed_seconds:.1f} sn) {cevap.text.splitlines()[0][:100]}")
        if not ok:
            print(f"       -> {sebep}")
            if cevap.hits:
                print(f"       -> getirilen: " + ", ".join(
                    f"{h.chunk.source}#{h.chunk.chunk_index}({h.score:.2f})" for h in cevap.hits
                ))
        print()

    ortalama = sum(sureler) / len(sureler)
    print("=" * 72)
    print(f"SONUC: {gecen}/{len(SORULAR)} — ortalama {ortalama:.1f} sn")
    return 0 if gecen == len(SORULAR) else 1


if __name__ == "__main__":
    raise SystemExit(main())
