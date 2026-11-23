"""Arama teşhisi: iki geliştirme setinde dört yapılandırma, k=8 parça, 3 koşu. Hiçbir ayarı değiştirmez.

Setler (yalnız cevaplı sorular):
  dev1 = evals/retrieval.yaml (alan: dogru)
  dev2 = evals/answers.yaml   (alan: dayanak)
Yapılandırmalar:
  BM25 + yeniden yazım (varsayılan hat), bge-m3 hibrit + yeniden yazım, yalnız bge-m3, düz BM25.
Her koşuda yeniden yazım soru başına BİR kez yapılır; iki "+ yeniden yazım" yapılandırması aynı
sorguları kullanır. Yalnız bge-m3 ve düz BM25 belirlenimcidir (model çağrısı yok).

Ölçüt: @8 = her dayanak gereksinimi, ilk 8 parçadan birinin maddesiyle karşılanıyor mu (parça düzeyi;
bağlama giden birim). Ayrıca her gereksinim için ilk parça sırası ve madde sırası kaydedilir.
dev2 için ek sütun: bağlam düzeyinde (context.kur, ceza tablosu ve tablo atfı eklemeleri dahil).

Çıktı: evals/teshis/sonuclar.json (+ evals/ARAMA_TESHIS.md, elle sınıflandırma ile birlikte)
Kullanım: python scripts/diagnose_retrieval.py [--runs 3]   (embedding kurulumu gerekir)
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

K = 8
OUT = ROOT / "evals" / "teshis"
CONFIGS = ("BM25 + yeniden yazım", "bge-m3 hibrit + yeniden yazım", "yalnız bge-m3", "düz BM25")


def soru_seti(ad: str) -> list[dict]:
    if ad == "dev1":
        qs = yaml.safe_load((ROOT / "evals/retrieval.yaml").read_text(encoding="utf-8"))["sorular"]
        return [{"id": q["id"], "tur": q["tur"], "soru": q["soru"], "req": q["dogru"]} for q in qs if q["tur"] != "cevapsiz"]
    qs = yaml.safe_load((ROOT / "evals/answers.yaml").read_text(encoding="utf-8"))["sorular"]
    return [{"id": q["id"], "tur": q.get("alt_tur") or q["tur"], "soru": q["soru"], "req": q["dayanak"]}
            for q in qs if q["tur"] != "cevapsiz"]


def key(c: dict) -> str:
    return f"{c['belge_kisa_ad']}:{c['madde_no']}"


def sirala(hits: list, req: list[list[str]]) -> dict:
    chunks = [getattr(h, "chunk", h) for h in hits]
    keys = [key(c) for c in chunks]
    arts = list(dict.fromkeys(keys))
    parca_sira, madde_sira = [], []
    for alts in req:
        ps = [i + 1 for i, k in enumerate(keys) if k in alts]
        ms = [i + 1 for i, k in enumerate(arts) if k in alts]
        parca_sira.append(min(ps) if ps else None)
        madde_sira.append(min(ms) if ms else None)
    return {"parca_sira": parca_sira, "madde_sira": madde_sira,
            "at8": all(s is not None and s <= K for s in parca_sira), "ilk8": [c["chunk_id"] for c in chunks[:K]]}


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=3)
    args = ap.parse_args()

    from mevzuat_rag.context import kur
    from mevzuat_rag.retrieve import Retriever
    from mevzuat_rag.rewrite import QueryRewriter

    bm25 = Retriever(load_model=False)
    bge = Retriever(model="bge-m3")
    rw = QueryRewriter()
    n = len(bm25.chunks)
    OUT.mkdir(parents=True, exist_ok=True)
    sonuc: dict = {"k": K, "setler": {}}

    for set_ad in ("dev1", "dev2"):
        qs = soru_seti(set_ad)
        sabit = {q["id"]: {"yalnız bge-m3": sirala(bge.search(q["soru"], k=n, mode="dense"), q["req"]),
                           "düz BM25": sirala(bm25.search(q["soru"], k=n, mode="bm25"), q["req"])} for q in qs}
        kosular = []
        for run in range(1, args.runs + 1):
            with ThreadPoolExecutor(max_workers=4) as ex:
                yazimlar = list(ex.map(lambda q: rw.rewrite(q["soru"]), qs))
            satirlar = []
            for q, y in zip(qs, yazimlar):
                ek = y.sorgular or None
                h_bm = bm25.search(q["soru"], k=n, mode="bm25", extra_queries=ek)
                h_hy = bge.search(q["soru"], k=n, mode="hybrid", extra_queries=ek)
                s = {"id": q["id"], "tur": q["tur"], "sorgular": y.sorgular, "atilan": y.atilan_sorgular,
                     "BM25 + yeniden yazım": sirala(h_bm, q["req"]),
                     "bge-m3 hibrit + yeniden yazım": sirala(h_hy, q["req"]),
                     **sabit[q["id"]]}
                if set_ad == "dev2":
                    b = kur(h_bm, q["soru"], bm25, k=K)
                    bkeys = {key(c) for c in b.parcalar}
                    s["baglam_bm25_yazim"] = all(any(a in bkeys for a in alts) for alts in q["req"])
                satirlar.append(s)
            kosular.append(satirlar)
            print(f"{set_ad} koşu {run}: " + "  ".join(
                f"{c.split(' ')[0]}{'+rw' if 'yazım' in c else ''}={sum(s[c]['at8'] for s in satirlar)}/{len(qs)}"
                for c in CONFIGS))
        sonuc["setler"][set_ad] = {"sorular": qs, "kosular": kosular}

    (OUT / "sonuclar.json").write_text(json.dumps(sonuc, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print("-> evals/teshis/sonuclar.json")


if __name__ == "__main__":
    main()
