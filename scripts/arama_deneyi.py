"""Arama değişikliği deneyi ve karar kuralı (docs/kararlar.md, "Arama değişikliği kabul kuralı").

Yapılandırmalar (BM25 tabanlı, Haiku yeniden yazım, k=8):
  0 varsayılan, 1 iki aşamalı RRF, 2 parça çeşitliliği (maddeden en fazla 2), 3 özgün ifade (prompt v4),
  4 = 1+2, 5 = 1+2+3; referans R = 1+2'nin bge-m3 hibrit karşılığı (karar dışı).
Her koşuda yeniden yazım soru başına bir kez (v3 ve v4 ayrı ayrı); aynı prompt'u kullanan bütün
yapılandırmalar aynı sorguları paylaşır (eşleştirilmiş karşılaştırma).

Kural bağlam düzeyinde uygulanır: set başına 3 koşunun medyanı; toplam = iki medyanın toplamı.
  (a) toplam kazanç >= 3, (b) hiçbir sette kayıp > 1 değil. Birden çoksa basitlik sırası: 2, 1, 3, 4, 5.

Çıktı: evals/arama_deneyi/sonuclar.json, evals/ARAMA_DENEYI.md
Kullanım: python scripts/arama_deneyi.py [--runs 3]   |   --rapor (kayıtlı sonuçtan yeniden üret)
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from diagnose_retrieval import K, key, soru_seti  # noqa: E402

OUT = ROOT / "evals" / "arama_deneyi"
CONFIGS = {
    "0 varsayılan":              dict(prompt=3, birlestirme="duz", div=None, mode="bm25"),
    "1 iki aşamalı RRF":         dict(prompt=3, birlestirme="iki_asamali", div=None, mode="bm25"),
    "2 parça çeşitliliği":       dict(prompt=3, birlestirme="duz", div=2, mode="bm25"),
    "3 özgün ifade (prompt v4)": dict(prompt=4, birlestirme="duz", div=None, mode="bm25"),
    "4 = 1+2":                   dict(prompt=3, birlestirme="iki_asamali", div=2, mode="bm25"),
    "5 = 1+2+3":                 dict(prompt=4, birlestirme="iki_asamali", div=2, mode="bm25"),
    "R bge-m3 hibrit, 1+2":      dict(prompt=3, birlestirme="iki_asamali", div=2, mode="hybrid"),
}
BASIT_SIRA = ["2 parça çeşitliliği", "1 iki aşamalı RRF", "3 özgün ifade (prompt v4)", "4 = 1+2", "5 = 1+2+3"]
BASELINE = "0 varsayılan"
SETLER = ("dev1", "dev2")


def kos(runs: int) -> dict:
    from mevzuat_rag.context import kur
    from mevzuat_rag.retrieve import Retriever
    from mevzuat_rag.rewrite import QueryRewriter

    bm25 = Retriever(load_model=False)
    bge = Retriever(model="bge-m3")
    yazicilar = {3: QueryRewriter(prompt_surumu=3), 4: QueryRewriter(prompt_surumu=4)}
    n = len(bm25.chunks)
    data: dict = {"k": K, "setler": {}}
    for s in SETLER:
        qs = soru_seti(s)
        kosular = []
        for run in range(1, runs + 1):
            yazim = {}
            for v, rw in yazicilar.items():
                with ThreadPoolExecutor(max_workers=4) as ex:
                    yazim[v] = list(ex.map(lambda q: rw.rewrite(q["soru"]), qs))
            satirlar = []
            for qi, q in enumerate(qs):
                row = {"id": q["id"], "sorgular": {v: yazim[v][qi].sorgular for v in yazim},
                       "atilan": {v: yazim[v][qi].atilan_sorgular for v in yazim}}
                for ad, c in CONFIGS.items():
                    r = bge if c["mode"] == "hybrid" else bm25
                    hits = r.search(q["soru"], k=n, mode=c["mode"], extra_queries=yazim[c["prompt"]][qi].sorgular or None,
                                    birlestirme=c["birlestirme"], max_parca_madde=c["div"])
                    ilk8 = [key(h.chunk) for h in hits[:K]]
                    b = kur(hits, q["soru"], bm25, k=K)
                    bkeys = {key(p) for p in b.parcalar}
                    row[ad] = {"arama": all(any(a in ilk8 for a in alts) for alts in q["req"]),
                               "baglam": all(any(a in bkeys for a in alts) for alts in q["req"]),
                               "ilk8": [h.chunk["chunk_id"] for h in hits[:K]]}
                satirlar.append(row)
            kosular.append(satirlar)
            print(f"{s} koşu {run}: " + "  ".join(
                f"{ad.split(' ')[0]}={sum(r[ad]['baglam'] for r in satirlar)}" for ad in CONFIGS))
        data["setler"][s] = {"sorular": qs, "kosular": kosular}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "sonuclar.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    return data


def ozet(data: dict, duzey: str) -> dict:
    """{config: {set: [koşu1, koşu2, koşu3]}}"""
    out = {}
    for ad in CONFIGS:
        out[ad] = {s: [sum(r[ad][duzey] for r in k) for k in data["setler"][s]["kosular"]] for s in SETLER}
    return out


def karar(data: dict) -> tuple[dict, str | None]:
    oz = ozet(data, "baglam")
    med = {ad: {s: statistics.median(v) for s, v in d.items()} for ad, d in oz.items()}
    b = med[BASELINE]
    sonuc = {}
    for ad in CONFIGS:
        if ad == BASELINE:
            continue
        fark = {s: med[ad][s] - b[s] for s in SETLER}
        toplam = sum(fark.values())
        a_ok = toplam >= 3
        b_ok = all(f >= -1 for f in fark.values())
        sonuc[ad] = {"fark": fark, "toplam": toplam, "a": a_ok, "b": b_ok,
                     "kabul": a_ok and b_ok and not ad.startswith("R")}
    secilen = next((ad for ad in BASIT_SIRA if sonuc[ad]["kabul"]), None)
    return sonuc, secilen


def cogunluk(data: dict, s: str, ad: str, duzey: str) -> dict[str, bool]:
    ks = data["setler"][s]["kosular"]
    ids = [r["id"] for r in ks[0]]
    return {i: sum(next(r for r in k if r["id"] == i)[ad][duzey] for k in ks) >= 2 for i in ids}


def rapor(data: dict) -> None:
    sonuc, secilen = karar(data)
    L = ["# Arama değişikliği deneyi\n",
         "`python scripts/arama_deneyi.py` tarafından üretilir. Kural ve uygulama ayrıntıları ölçümden önce "
         "`docs/kararlar.md`'ye kaydedildi. k=8, 3 koşu; yeniden yazım Haiku 5.5. Hücreler: medyan (en düşük–en yüksek).\n",
         "## 1. Sonuçlar\n"]
    for duzey, baslik in (("baglam", "Bağlam düzeyi (kural bu düzeyde uygulanır)"), ("arama", "Arama düzeyi (@8, bilgi için)")):
        oz = ozet(data, duzey)
        L += [f"### {baslik}\n", "| Yapılandırma | dev1 (26) | dev2 (15) | Toplam (41) |", "|---|---|---|---|"]
        for ad, d in oz.items():
            m1, m2 = statistics.median(d["dev1"]), statistics.median(d["dev2"])
            cell = lambda v: f"{statistics.median(v):g} ({min(v)}–{max(v)})"
            bold = "**" if ad == secilen else ""
            L.append(f"| {bold}{ad}{bold} | {cell(d['dev1'])} | {cell(d['dev2'])} | {m1 + m2:g} |")
        L.append("")
    L += ["## 2. Karar kuralı\n",
          "(a) toplamda varsayılana göre en az +3, (b) hiçbir sette −1'den fazla kayıp yok. Bağlam düzeyi, medyanlar.\n",
          "| Yapılandırma | dev1 farkı | dev2 farkı | Toplam | (a) | (b) | Sonuç |", "|---|---|---|---|---|---|---|"]
    for ad, r in sonuc.items():
        durum = "referans (seçilemez)" if ad.startswith("R") else ("**kabul**" if r["kabul"] else "ret")
        L.append(f"| {ad} | {r['fark']['dev1']:+g} | {r['fark']['dev2']:+g} | {r['toplam']:+g} | "
                 f"{'✓' if r['a'] else '✗'} | {'✓' if r['b'] else '✗'} | {durum} |")
    L.append("")
    L.append(f"**Seçilen:** {secilen or 'hiçbiri — varsayılan değişmez'}"
             + (" (koşulu sağlayanlar arasında basitlik sırasına göre ilk)" if secilen else "") + "\n")

    L += ["## 3. Kazanılan ve kaybedilen sorular (bağlam düzeyi, 3 koşunun çoğunluğu)\n",
          "| Yapılandırma | Set | Kazanılan | Kaybedilen |", "|---|---|---|---|"]
    for ad in CONFIGS:
        if ad == BASELINE:
            continue
        for s in SETLER:
            b = cogunluk(data, s, BASELINE, "baglam")
            c = cogunluk(data, s, ad, "baglam")
            kaz = [i for i in b if c[i] and not b[i]]
            kay = [i for i in b if b[i] and not c[i]]
            L.append(f"| {ad} | {s} | {', '.join(kaz) or '—'} | {', '.join(kay) or '—'} |")
    L.append("")
    yorum = ROOT / "evals" / "arama_deneyi_yorum.md"
    if yorum.exists():
        L.append(yorum.read_text(encoding="utf-8"))
    (ROOT / "evals" / "ARAMA_DENEYI.md").write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
    print("rapor -> evals/ARAMA_DENEYI.md;", "seçilen:", secilen)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--rapor", action="store_true")
    args = ap.parse_args()
    data = (json.loads((OUT / "sonuclar.json").read_text(encoding="utf-8")) if args.rapor else kos(args.runs))
    rapor(data)


if __name__ == "__main__":
    main()
