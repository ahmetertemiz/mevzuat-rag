"""Komut satırından arama denemesi.

    python search.py "cayma hakkı kaç gün"
    python search.py "6502 m.48" --mode bm25 -k 3

Henüz model çağrısı ve cevap üretimi yok; yalnızca en ilgili parçalar listelenir.
"""
from __future__ import annotations

import argparse
import sys
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from mevzuat_rag.retrieve import MODES, Retriever  # noqa: E402


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Mevzuat parçalarında arama")
    ap.add_argument("sorgu")
    ap.add_argument("-k", type=int, default=5, help="döndürülecek parça sayısı (varsayılan 5)")
    ap.add_argument("--mode", choices=MODES, default="hybrid")
    ap.add_argument("--uzun", action="store_true", help="parça metninin tamamını göster")
    args = ap.parse_args()

    r = Retriever(load_model=args.mode != "bm25")
    for h in r.search(args.sorgu, k=args.k, mode=args.mode):
        c = h.chunk
        ranks = []
        if h.dense_rank:
            ranks.append(f"dense #{h.dense_rank}")
        if h.bm25_rank:
            ranks.append(f"bm25 #{h.bm25_rank}")
        print(f"\n[{h.rank}] {c['chunk_id']}  skor={h.score:.4f}  ({', '.join(ranks)})")
        print(f"    {c['baglam_basligi']}")
        body = c["metin"] if args.uzun else textwrap.shorten(c["metin"], 300, placeholder=" …")
        print(textwrap.indent(textwrap.fill(body, 100) if not args.uzun else body, "    "))
        if c["dipnotlar"]:
            print("    dipnotlar: " + ", ".join(f"{d['no']} ({d['tur']})" for d in c["dipnotlar"]))


if __name__ == "__main__":
    main()
