"""Komut satırından arama denemesi.

    python search.py "cayma hakkı kaç gün"                 # varsayılan: BM25 + yeniden yazım
    python search.py "6502 m.48" --yeniden-yazma -k 3       # yalnız BM25, model çağrısı yok
    python search.py "cayma hakkı" --mode hybrid            # embedding (requirements-embedding.txt)

Henüz cevap üretimi yok; yalnızca en ilgili parçalar listelenir.
"""
from __future__ import annotations

import argparse
import sys
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from mevzuat_rag import config  # noqa: E402
from mevzuat_rag.pipeline import Arayici  # noqa: E402
from mevzuat_rag.retrieve import MODES  # noqa: E402


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Mevzuat parçalarında arama")
    ap.add_argument("sorgu")
    ap.add_argument("-k", type=int, default=5, help="döndürülecek parça sayısı (varsayılan 5)")
    ap.add_argument("--mode", choices=MODES, default=config.DEFAULT_SEARCH_MODE,
                    help=f"arama modu (varsayılan {config.DEFAULT_SEARCH_MODE}); dense/hybrid embedding kurulumu ister")
    ap.add_argument("--model", choices=list(config.EMBED_MODELS), default=config.DEFAULT_EMBED,
                    help="dense/hybrid için embedding modeli")
    ap.add_argument("--yeniden-yazma", action="store_true",
                    help="sorgu yeniden yazımını kapat (model çağrısı yapılmaz)")
    ap.add_argument("--uzun", action="store_true", help="parça metninin tamamını göster")
    args = ap.parse_args()

    arayici = Arayici(mode=args.mode, rewrite=not args.yeniden_yazma, embed_model=args.model)
    s = arayici.ara(args.sorgu, k=args.k)

    print(f"mod: {s.mode} · yeniden yazım: {s.yeniden_yazim}")
    if s.sorgular:
        print(f"üretilen sorgular: {s.sorgular}  (maliyet ${s.maliyet_usd:.5f}, {s.yeniden_yazim_sn:.1f} sn)")
    for a in s.atilan_sorgular:
        print(f"atılan sorgu: {a['sorgu']!r} ({a['neden']})")
    if s.uyari:
        print(f"UYARI: {s.uyari}")
    if not s.hits:
        print("\nEşleşen parça bulunamadı.")
    for h in s.hits:
        c = h.chunk
        ranks = []
        pre = "özgün soruda " if s.sorgular else ""  # birleşik sırayla karışmasın
        if h.dense_rank:
            ranks.append(f"{pre}dense #{h.dense_rank}")
        if h.bm25_rank:
            ranks.append(f"{pre}bm25 #{h.bm25_rank}")
        print(f"\n[{h.rank}] {c['chunk_id']}  skor={h.score:.4f}" + (f"  ({', '.join(ranks)})" if ranks else ""))
        print(f"    {c['baglam_basligi']}")
        body = c["metin"] if args.uzun else textwrap.shorten(c["metin"], 300, placeholder=" …")
        print(textwrap.indent(textwrap.fill(body, 100) if not args.uzun else body, "    "))
        if c["dipnotlar"]:
            print("    dipnotlar: " + ", ".join(f"{d['no']} ({d['tur']})" for d in c["dipnotlar"]))


if __name__ == "__main__":
    main()
