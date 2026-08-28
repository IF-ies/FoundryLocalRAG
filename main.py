"""FoundryLocalRAG CLI.

Kullanım:
    python main.py check                 # ortam ve model kontrolü
    python main.py ingest [--reset]      # corpus/ klasörünü veritabanına yükle
    python main.py ask "soru"            # tek soru sor
    python main.py chat                  # soru-cevap döngüsü
    python main.py status                # veritabanında ne var
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from foundry_rag import config, db, rag  # noqa: E402
from foundry_rag.ingest import ingest_corpus  # noqa: E402


def _client():
    from foundry_rag.client import FoundryClient

    print("Foundry Local hazırlanıyor (ilk çalıştırmada model indirilir)...")
    client = FoundryClient(progress=print)
    print(f"  chat      : {client.chat_model_id}")
    print(f"  embedding : {client.embed_model_id}")
    return client


def cmd_check(_args: argparse.Namespace) -> int:
    client = _client()

    vector = client.embed_one("merhaba dünya")
    print(f"  embedding boyutu: {len(vector)}")

    reply = client.chat(
        # Soru DÜZGÜN Türkçe yazılmalı: diakritiksiz ASCII ile sorulduğunda
        # küçük modeller anlamsız tekrar döngüsüne giriyor (ölçüldü).
        [{"role": "user", "content": "Türkiye'nin başkenti neresidir? Tek kelimeyle cevapla."}]
    )
    print(f"  chat testi: {reply!r}")
    print("Ortam hazır.")
    return 0


def cmd_ingest(args: argparse.Namespace) -> int:
    conn = db.connect()
    if args.reset:
        db.clear(conn)
        conn.commit()
        print("Veritabanı temizlendi.")

    client = _client()
    print(f"Corpus: {config.CORPUS_DIR}")
    report = ingest_corpus(client, conn, progress=print)
    print(report.summary())
    print(f"Veritabanındaki toplam chunk: {db.count(conn)}")
    for source, n in db.sources(conn):
        print(f"  {source}: {n}")
    return 0 if report.chunks else 1


def _print_answer(answer: rag.Answer) -> None:
    print()
    print(answer.text)
    if answer.hits:
        print()
        print("Getirilen parçalar:")
        for hit in answer.hits:
            preview = hit.chunk.content[:70].replace("\n", " ")
            print(f"  [{hit.score:.3f}] {hit.chunk.source}#{hit.chunk.chunk_index} — {preview}...")
    print(f"({answer.elapsed_seconds:.2f} sn)")


def cmd_ask(args: argparse.Namespace) -> int:
    conn = db.connect()
    client = _client()
    answer = rag.answer_query(client, conn, args.question)
    _print_answer(answer)
    return 0


def cmd_chat(_args: argparse.Namespace) -> int:
    conn = db.connect()
    if db.count(conn) == 0:
        print("Veritabanı boş. Önce: python main.py ingest")
        return 1
    client = _client()
    print("\nSorularını yaz. Çıkmak için 'q' veya Ctrl+C.\n")
    while True:
        try:
            question = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if question.lower() in {"q", "quit", "exit", "çık"}:
            break
        if not question:
            continue
        _print_answer(rag.answer_query(client, conn, question))
        print()
    client.unload()
    return 0


def cmd_status(_args: argparse.Namespace) -> int:
    conn = db.connect()
    total = db.count(conn)
    print(f"Veritabanı: {config.DB_PATH}")
    print(f"Toplam chunk: {total}")
    for source, n in db.sources(conn):
        print(f"  {source}: {n}")
    if total == 0:
        print("(boş — python main.py ingest)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="foundry-rag", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("check", help="ortam ve model kontrolü").set_defaults(func=cmd_check)

    p_ingest = sub.add_parser("ingest", help="corpus klasörünü yükle")
    p_ingest.add_argument("--reset", action="store_true", help="önce veritabanını temizle")
    p_ingest.set_defaults(func=cmd_ingest)

    p_ask = sub.add_parser("ask", help="tek soru sor")
    p_ask.add_argument("question", help="soru metni")
    p_ask.set_defaults(func=cmd_ask)

    sub.add_parser("chat", help="soru-cevap döngüsü").set_defaults(func=cmd_chat)
    sub.add_parser("status", help="veritabanı özeti").set_defaults(func=cmd_status)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
