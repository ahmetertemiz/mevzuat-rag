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

from mevzuat_rag import config  # noqa: E402
from mevzuat_rag.retrieve import MODES, Retriever  # noqa: E402


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Mevzuat parçalarında arama")
    ap.add_argument("sorgu")
    ap.add_argument("-k", type=int, default=5, help="döndürülecek parça sayısı (varsayılan 5)")
    ap.add_argument("--mode", choices=MODES, default="hybrid")
    ap.add_argument("--model", choices=list(config.EMBED_MODELS), default=config.DEFAULT_EMBED,
                    help="embedding modeli (varsayılan bge-m3)")
    ap.add_argument("--yeniden-yaz", action="store_true",
                    help="soruyu önce model çağrısıyla mevzuat diline çevir (API anahtarı gerekir)")
    ap.add_argument("--uzun", action="store_true", help="parça metninin tamamını göster")
    args = ap.parse_args()

    extra = None
    if args.yeniden_yaz:
        from mevzuat_rag.rewrite import QueryRewriter

        rw = QueryRewriter().rewrite(args.sorgu)
        extra = rw.sorgular
        print(f"üretilen sorgular: {extra}  (maliyet ${rw.cost_usd:.4f}, {rw.seconds:.1f} sn)")
    r = Retriever(model=args.model, load_model=args.mode != "bm25")
    for h in r.search(args.sorgu, k=args.k, mode=args.mode, extra_queries=extra):
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
