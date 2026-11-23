"""Atıf takibi deneyi ve kabul kuralı (docs/kararlar.md, "Atıf takibi kabul kuralı").

Her koşuda yeniden yazım soru başına BİR kez yapılır (dondurulmuş varsayılan hat); atıf takipli ve
takipsiz bağlam aynı arama sonucundan kurulur.
  (a) Bağlam düzeyi: dev1 (26) + dev2 (15), 3 koşu, set başına medyan; toplam kazanç >= 2.
  (b) Cevap: dev2'nin 20 sorusu, Haiku 5.5, 3 koşu; aynı aramayla iki kol (kapalı / açık).
      Yanlış olgu elle okunur (evals/atif_elle_okuma.yaml); açık kolun toplamı kapalıdan büyük olmamalı.

Çıktı: evals/atif_deneyi/*.json, evals/ATIF_DENEYI.md
Kullanım: python scripts/atif_deneyi.py [--runs 3]   |   --rapor
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from diagnose_retrieval import K, key, soru_seti  # noqa: E402
from eval_answers import olc  # noqa: E402

OUT = ROOT / "evals" / "atif_deneyi"
KOLLAR = ("kapali", "acik")
SETLER = ("dev1", "dev2")
MODEL = "claude-haiku-5-5"


def kos(runs: int, workers: int = 4) -> None:
    from mevzuat_rag.answer import Cevaplayici, cevap_sozlugu
    from mevzuat_rag.context import kur
    from mevzuat_rag.pipeline import Arayici

    arayici = Arayici()
    r = arayici.retriever
    dev2_tum = yaml.safe_load((ROOT / "evals/answers.yaml").read_text(encoding="utf-8"))["sorular"]
    cv = {kol: Cevaplayici(arayici=arayici, model=MODEL, atif_takibi=(kol == "acik")) for kol in KOLLAR}
    OUT.mkdir(parents=True, exist_ok=True)
    baglam: dict = {s: [] for s in SETLER}
    for run in range(1, runs + 1):
        # dev1: yalnız bağlam düzeyi
        qs = soru_seti("dev1")
        with ThreadPoolExecutor(max_workers=workers) as ex:
            aramalar = list(ex.map(lambda q: arayici.ara(q["soru"], k=K), qs))
        baglam["dev1"].append(_baglam_satirlari(qs, aramalar, r, kur))
        # dev2: 20 sorunun hepsi aranır; bağlam ölçümü cevaplı 15'te, cevaplar 20'de
        with ThreadPoolExecutor(max_workers=workers) as ex:
            aramalar2 = list(ex.map(lambda q: arayici.ara(q["soru"], k=K), dev2_tum))
        qs2 = soru_seti("dev2")
        ara2 = {q["id"]: a for q, a in zip(dev2_tum, aramalar2)}
        baglam["dev2"].append(_baglam_satirlari(qs2, [ara2[q["id"]] for q in qs2], r, kur))
        for kol in KOLLAR:
            with ThreadPoolExecutor(max_workers=workers) as ex:
                cevaplar = list(ex.map(lambda qa: cevap_sozlugu(cv[kol].cevapla_aramayla(qa[0]["soru"], qa[1])),
                                       zip(dev2_tum, aramalar2)))
            for q, c in zip(dev2_tum, cevaplar):
                c["id"] = q["id"]
            (OUT / f"cevap_{kol}_kosu{run}.json").write_text(
                json.dumps(cevaplar, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
        print(f"koşu {run}: " + "  ".join(
            f"{s} {kol}={sum(x[kol] for x in baglam[s][-1])}" for s in SETLER for kol in KOLLAR))
    (OUT / "baglam.json").write_text(json.dumps(baglam, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")


def _baglam_satirlari(qs, aramalar, r, kur) -> list[dict]:
    out = []
    for q, a in zip(qs, aramalar):
        row = {"id": q["id"], "sorgular": a.sorgular}
        for kol in KOLLAR:
            b = kur(a.hits, q["soru"], r, k=K, atif_takibi=(kol == "acik"))
            keys = {key(p) for p in b.parcalar}
            row[kol] = all(any(x in keys for x in alts) for alts in q["req"])
            row[f"{kol}_ek"] = b.ek_parcalar
        out.append(row)
    return out


def rapor() -> None:
    baglam = json.loads((OUT / "baglam.json").read_text(encoding="utf-8"))
    L = ["# Atıf takibi deneyi\n",
         "`python scripts/atif_deneyi.py` tarafından üretilir. Kural ölçümden önce `docs/kararlar.md`'ye "
         "kaydedildi. k=8, 3 koşu, yeniden yazım Haiku 5.5 (prompt v3); iki kol aynı aramayı paylaşır.\n",
         "## 1. Bağlam düzeyi (kural a)\n",
         "| Set | Kapalı (koşular) | Açık (koşular) | Medyan farkı |", "|---|---|---|---|"]
    toplam = 0
    for s in SETLER:
        k = [sum(x["kapali"] for x in run) for run in baglam[s]]
        a = [sum(x["acik"] for x in run) for run in baglam[s]]
        fark = statistics.median(a) - statistics.median(k)
        toplam += fark
        L.append(f"| {s} | {' / '.join(map(str, k))} (medyan {statistics.median(k):g}) | "
                 f"{' / '.join(map(str, a))} (medyan {statistics.median(a):g}) | {fark:+g} |")
    a_ok = toplam >= 2
    L += ["", f"**Toplam kazanç: {toplam:+g}** (eşik +2) → (a) {'sağlandı' if a_ok else 'sağlanmadı'}\n",
          "### Değişen sorular (koşu sırasıyla; K = kapalı, A = açık)\n",
          "| Set | Soru | Kapalı | Açık | Açıkta eklenen atıf parçaları (koşu 1) |", "|---|---|---|---|---|"]
    for s in SETLER:
        ids = [x["id"] for x in baglam[s][0]]
        for i in ids:
            rows = [next(x for x in run if x["id"] == i) for run in baglam[s]]
            k = "".join("✓" if x["kapali"] else "✗" for x in rows)
            a = "".join("✓" if x["acik"] else "✗" for x in rows)
            if k != a:
                ek = [e for e in rows[0]["acik_ek"] if e not in rows[0]["kapali_ek"]]
                L.append(f"| {s} | {i} | {k} | {a} | {', '.join(ek) or '—'} |")
    eklenen_soru = {s: [sum(bool(set(x["acik_ek"]) - set(x["kapali_ek"])) for x in run) for run in baglam[s]]
                    for s in SETLER}
    L += ["", "Atıf eki alan soru sayısı (koşu başına): " +
          "; ".join(f"{s} {eklenen_soru[s]}" for s in SETLER) + "\n"]

    # --- cevap
    qs = {q["id"]: q for q in yaml.safe_load((ROOT / "evals/answers.yaml").read_text(encoding="utf-8"))["sorular"]}
    with (ROOT / "data" / "chunks.jsonl").open(encoding="utf-8") as f:
        chunks = {c["chunk_id"]: c for c in map(json.loads, f)}
    olcum = {kol: [[olc(qs[c["id"]], c, chunks) for c in json.loads(p.read_text(encoding="utf-8"))]
                   for p in sorted(OUT.glob(f"cevap_{kol}_kosu*.json"))] for kol in KOLLAR}
    elle = {}
    ep = ROOT / "evals" / "atif_elle_okuma.yaml"
    if ep.exists():
        elle = yaml.safe_load(ep.read_text(encoding="utf-8")) or {}

    def oz(xs):
        return f"{min(xs):g} / {statistics.median(xs):g} / {max(xs):g}"
    satirlar = [
        ("Yanlış olgu (elle okuma; koşu başına)",
         lambda kol: [len((elle.get(kol) or {}).get(f"kosu{i}", {}).get("yanlis_bilgi") or [])
                      for i in range(1, len(olcum[kol]) + 1)] if elle else None),
        ("Madde doğruluğu (cevaplı 15)", lambda kol: [sum(r["madde_dogru"] for r in run) for run in olcum[kol]]),
        ("Yanlış reddetme (cevaplı 15)", lambda kol: [sum(r["yanlis_ret"] for r in run) for run in olcum[kol]]),
        ("Doğru reddetme (cevapsız 5)", lambda kol: [sum(r["dogru_ret"] for r in run) for run in olcum[kol]]),
        ("Bağlamda (cevaplı 15)", lambda kol: [sum(r["baglamda"] for r in run) for run in olcum[kol]]),
        ("Olgu oranı (%)", lambda kol: [round(100 * sum(r["olgu_bulunan"] for r in run) /
                                              max(1, sum(r["olgu_toplam"] for r in run))) for run in olcum[kol]]),
        ("Çıkarılan cümle", lambda kol: [sum(r["cumle_cikarilan"] for r in run) for run in olcum[kol]]),
    ]
    L += ["## 2. Cevap değerlendirmesi (kural b; dev2, Haiku 5.5, 3 koşu)\n",
          "| Ölçüt | Kapalı | Açık |", "|---|---|---|"]
    yo = {}
    for ad, fn in satirlar:
        h = {kol: fn(kol) for kol in KOLLAR}
        if ad.startswith("Yanlış olgu"):
            yo = h
        L.append(f"| {ad} | " + " | ".join(
            (f"{oz(h[kol])} (toplam {sum(h[kol])})" if ad.startswith("Yanlış olgu") else oz(h[kol]))
            if h[kol] else "—" for kol in KOLLAR) + " |")
    b_ok = None
    if yo.get("kapali") is not None and yo.get("acik") is not None:
        b_ok = sum(yo["acik"]) <= sum(yo["kapali"])
        L += ["", f"**Yanlış olgu toplamı: kapalı {sum(yo['kapali'])}, açık {sum(yo['acik'])}** → (b) "
              f"{'sağlandı' if b_ok else 'sağlanmadı'}"]
    L += ["", "## 3. Karar\n",
          ("**Kabul**: atıf takibi varsayılan olur." if (a_ok and b_ok) else
           "**Ret**: atıf takibi varsayılan olmaz (kod kapalı seçenek olarak kalır)." if b_ok is not None or not a_ok
           else "Elle okuma bekleniyor."), ""]
    yorum = ROOT / "evals" / "atif_deneyi_yorum.md"
    if yorum.exists():
        L.append(yorum.read_text(encoding="utf-8"))
    (ROOT / "evals" / "ATIF_DENEYI.md").write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
    print("rapor -> evals/ATIF_DENEYI.md; (a)", a_ok, "(b)", b_ok)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--rapor", action="store_true")
    args = ap.parse_args()
    if not args.rapor:
        kos(args.runs)
    rapor()


if __name__ == "__main__":
    main()
