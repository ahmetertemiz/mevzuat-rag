"""Holdout'un tek seferlik koşusu (dondurulmuş sistem, etiket `sistem-donduruldu-holdout`).

Arama: `eval_retrieval.py --varsayilan --runs 3` ile aynı tanım (önbelleksiz, canlı yeniden yazım,
@k = doğru madde(ler) maddeye indirgenmiş ilk k sonuçta) + k=8'de bağlam düzeyi (`context.kur`).
Cevap: 20 sorunun her biri için Haiku 5.5 ile tek koşu; 1. arama koşusunun sonuçları kullanılır
(ayrı bir yeniden yazım çağrısı yapılmaz). Cevaplar evals/holdout_cevaplari/ altına yazılır;
elle değerlendirilmez, yalnız otomatik ölçütler raporlanır.

Kullanım: python scripts/holdout.py            (koşar; YALNIZ BİR KEZ)
          python scripts/holdout.py --rapor    (kayıtlı sonuçtan raporu yeniden üretir)
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

from eval_retrieval import KS, ranked_articles  # noqa: E402

OUT = ROOT / "evals" / "holdout_cevaplari"
K = 8
RUNS = 3


def _key(p: dict) -> str:
    return f"{p['belge_kisa_ad']}:{p['madde_no']}"


def kos(questions: list[dict]) -> dict:
    from mevzuat_rag.answer import Cevaplayici, cevap_sozlugu
    from mevzuat_rag.context import kur
    from mevzuat_rag.pipeline import Arayici

    arayici = Arayici()
    r = arayici.retriever
    n = len(r.chunks)
    kosular, ilk_aramalar = [], None
    for run in range(1, RUNS + 1):
        with ThreadPoolExecutor(max_workers=4) as ex:
            aramalar = list(ex.map(lambda q: arayici.ara(q["soru"], k=n), questions))
        if ilk_aramalar is None:
            ilk_aramalar = aramalar
        rows = []
        for q, s in zip(questions, aramalar):
            keys = [k for k, _ in ranked_articles(s.hits)]
            ranks = []
            for req in q["dogru"]:
                rr = [keys.index(x) + 1 for x in req if x in keys]
                ranks.append(min(rr) if rr else None)
            b = kur(s.hits, q["soru"], r, k=K)
            bkeys = {_key(p) for p in b.parcalar}
            row = {"id": q["id"], "tur": q["tur"], "siralar": ranks, "ilk5": keys[:5],
                   "yeniden_yazim": s.yeniden_yazim, "sorgular": s.sorgular, "uyari": s.uyari,
                   "maliyet_usd": s.maliyet_usd, "baglam_parcalari": [p["chunk_id"] for p in b.parcalar],
                   "baglam8": bool(q["dogru"]) and all(any(a in bkeys for a in alts) for alts in q["dogru"])}
            for k in KS:
                met = [x is not None and x <= k for x in ranks]
                row[f"@{k}"] = bool(met) and all(met)
            rows.append(row)
        kosular.append(rows)
        cev = [x for x in rows if x["tur"] != "cevapsiz"]
        print(f"arama koşu {run}: " + "  ".join(f"@{k}={sum(x[f'@{k}'] for x in cev)}" for k in KS)
              + f"  bağlam@8={sum(x['baglam8'] for x in cev)}/{len(cev)}")

    cv = Cevaplayici(arayici=arayici, model="claude-haiku-5-5")
    OUT.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=4) as ex:
        cevaplar = list(ex.map(lambda qs: cevap_sozlugu(cv.cevapla_aramayla(qs[0]["soru"], qs[1])),
                               zip(questions, ilk_aramalar)))
    for q, c in zip(questions, cevaplar):
        c["id"] = q["id"]
        (OUT / f"{q['id']}.json").write_text(json.dumps(c, ensure_ascii=False, indent=1),
                                             encoding="utf-8", newline="\n")
    data = {"arama_kosulari": kosular, "cevap_modeli": cv.model, "cevap_atif_takibi": cv.atif_takibi}
    (OUT / "arama_sonuclari.json").write_text(json.dumps(data, ensure_ascii=False, indent=1),
                                              encoding="utf-8", newline="\n")
    print("cevaplar ->", OUT)
    return data


def cevap_olcutleri(cevaplar: list[dict], cevapsiz_ids: set[str]) -> dict:
    tum_alinti = [d for c in cevaplar for cm in c["cumleler"] + c["cikarilan_cumleler"] for d in cm["dayanaklar"]]
    durum = {d: sum(c["durum"] == d for c in cevaplar if c["id"] not in cevapsiz_ids)
             for d in ("cevaplandi", "kismen_cevaplandi", "bulunamadi")}
    return {
        "durum": durum,
        "alinti_orani": round(100 * sum(d["dogrulandi"] for d in tum_alinti) / max(1, len(tum_alinti)), 1),
        "alinti_toplam": len(tum_alinti),
        "cikarilan": sum(len(c["cikarilan_cumleler"]) for c in cevaplar),
        "cumle_toplam": sum(len(c["cumleler"]) + len(c["cikarilan_cumleler"]) for c in cevaplar),
        "cikarilan_cevap": sum(bool(c["cikarilan_cumleler"]) for c in cevaplar),
        "ret": sum(c["durum"] == "bulunamadi" for c in cevaplar if c["id"] in cevapsiz_ids),
        "sistem_hatasi": sum(any(u["tur"] == "sistem_hatasi" for u in c["uyarilar"]) for c in cevaplar),
    }


def _oz(xs) -> str:
    return f"{min(xs)} / {statistics.median(xs):g} / {max(xs)}"


def rapor(questions: list[dict]) -> None:
    data = json.loads((OUT / "arama_sonuclari.json").read_text(encoding="utf-8"))
    kos_ = data["arama_kosulari"]
    cev_ids = [q["id"] for q in questions if q["tur"] != "cevapsiz"]
    cevapsiz = {q["id"] for q in questions if q["tur"] == "cevapsiz"}
    per = [{x["id"]: x for x in rows} for rows in kos_]

    def say(k, ids=cev_ids):
        return [sum(p[i][k] for i in ids) for p in per]

    # geliştirme setleri: aynı sistemle en son ölçümler
    dev1 = json.loads((ROOT / "evals/sonuclar_retrieval_varsayilan.json").read_text(encoding="utf-8"))["ozet"]
    atif = json.loads((ROOT / "evals/atif_deneyi/baglam.json").read_text(encoding="utf-8"))
    dev_baglam = {s: [sum(x["kapali"] for x in run) for run in atif[s]] for s in ("dev1", "dev2")}
    dev2_kos = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((ROOT / "evals/atif_deneyi").glob("cevap_kapali_kosu*.json"))]
    dev2_cevapsiz = {q["id"] for q in yaml.safe_load((ROOT / "evals/answers.yaml").read_text(encoding="utf-8"))["sorular"]
                     if q["tur"] == "cevapsiz"}
    dev2_ol = [cevap_olcutleri(k, dev2_cevapsiz) for k in dev2_kos]
    cevaplar = [json.loads((OUT / f"{q['id']}.json").read_text(encoding="utf-8")) for q in questions]
    h = cevap_olcutleri(cevaplar, cevapsiz)

    nc, n1, n2 = len(cev_ids), 26, 15
    L = ["# Holdout raporu\n",
         "Sistem `sistem-donduruldu-holdout` etiketinde donduruldu ve holdout (`evals/holdout.yaml`, "
         f"{len(questions)} soru: "
         f"{nc} cevaplı, {len(cevapsiz)} cevapsız) **bir kez** koşuldu: `python scripts/holdout.py`. "
         "Hat: BM25 + yeniden yazım (Haiku 5.5, prompt v3), k=8, atıf takibi kapalı; cevap Haiku 5.5. "
         "Holdout sonuçlarına göre hiçbir şey değiştirilmedi.\n",
         "**Setin kaynağı:** Sorular proje sahibi yerine sohbetteki Claude tarafından yazıldı; yazan "
         "geliştirme setlerini görmüştü (sınır `evals/holdout.yaml` başında). Bu nedenle holdout tam "
         "bağımsız değil.\n",
         "Hücreler: en düşük / medyan / en yüksek (3 koşu). Yüzdeler medyandan.\n",
         "## 1. Arama\n",
         f"| Ölçüt | dev1 ({n1}) | dev2 ({n2}) | **holdout ({nc})** |", "|---|---|---|---|"]
    for k in KS:
        d1 = dev1[f"@{k}"]
        hv = say(f"@{k}")
        L.append(f"| @{k} | {_oz(d1)} (%{100 * statistics.median(d1) / n1:.0f}) | — | "
                 f"**{_oz(hv)} (%{100 * statistics.median(hv) / nc:.0f})** |")
    hb = say("baglam8")
    L.append(f"| Bağlam düzeyi, k=8 | {_oz(dev_baglam['dev1'])} (%{100 * statistics.median(dev_baglam['dev1']) / n1:.0f}) | "
             f"{_oz(dev_baglam['dev2'])} (%{100 * statistics.median(dev_baglam['dev2']) / n2:.0f}) | "
             f"**{_oz(hb)} (%{100 * statistics.median(hb) / nc:.0f})** |")
    L += ["", "dev1 @k: `evals/RAPOR_retrieval_varsayilan.md`; bağlam düzeyi: aynı sistemin son ölçümü "
          "(`evals/ATIF_DENEYI.md`, takipsiz kol). dev2 için @1/@3/@5 ölçülmedi (dayanak alanı bağlam "
          "düzeyinde kullanılır).\n"]
    turler = [t for t in ("madde_dili", "gunluk_dil", "iki_madde") if any(q["tur"] == t for q in questions)]
    L += ["### Türe göre (holdout)\n", "| Tür | n | @1 | @3 | @5 | Bağlam k=8 |", "|---|---|---|---|---|---|"]
    for t in turler:
        ids = [q["id"] for q in questions if q["tur"] == t]
        L.append(f"| {t} | {len(ids)} | " + " | ".join(_oz(say(f"@{k}", ids)) for k in KS)
                 + f" | {_oz(say('baglam8', ids))} |")
    L += ["", "### Soru bazında (koşu sırasıyla)\n", "| Soru | Tür | Doğru maddenin sırası | @5 | Bağlam k=8 |",
          "|---|---|---|---|---|"]
    for q in questions:
        if q["tur"] == "cevapsiz":
            continue
        cells = ["/".join("–" if x is None else str(x) for x in p[q["id"]]["siralar"]) for p in per]
        L.append(f"| {q['id']} | {q['tur']} | {', '.join(cells)} | "
                 + "".join("✓" if p[q["id"]]["@5"] else "✗" for p in per) + " | "
                 + "".join("✓" if p[q["id"]]["baglam8"] else "✗" for p in per) + " |")
    L += ["", "## 2. Cevap (otomatik ölçütler; elle okuma ayrıca yapılacak)\n",
          "Holdout: tek koşu, 1. arama koşusunun bağlamıyla. dev2: aynı sistem, 3 koşu "
          "(`evals/atif_deneyi/cevap_kapali_kosu*.json`).\n",
          f"| Ölçüt | dev2 ({n2} cevaplı + {len(dev2_cevapsiz)} cevapsız) | **holdout ({nc} + {len(cevapsiz)})** |",
          "|---|---|---|"]
    for d, ad in (("cevaplandi", "Cevaplandı"), ("kismen_cevaplandi", "Kısmen cevaplandı"), ("bulunamadi", "Bulunamadı (cevaplı soruda)")):
        L.append(f"| {ad} | {_oz([o['durum'][d] for o in dev2_ol])} | **{h['durum'][d]}** |")
    L += [f"| Alıntı doğrulama oranı (%) | {_oz([o['alinti_orani'] for o in dev2_ol])} | "
          f"**{h['alinti_orani']}** ({h['alinti_toplam']} alıntı) |",
          f"| Çıkarılan cümle | {_oz([o['cikarilan'] for o in dev2_ol])} | **{h['cikarilan']}** / {h['cumle_toplam']} cümle "
          f"({h['cikarilan_cevap']} cevapta) |",
          f"| Cevapsız soruda reddetme | {_oz([o['ret'] for o in dev2_ol])} / {len(dev2_cevapsiz)} | "
          f"**{h['ret']} / {len(cevapsiz)}** |",
          f"| Sistem hatası (okunamayan çıktı) | {_oz([o['sistem_hatasi'] for o in dev2_ol])} | **{h['sistem_hatasi']}** |",
          "", "### Soru bazında durum (holdout)\n", "| Soru | Tür | Durum | Gösterilen / çıkarılan cümle | Uyarılar |",
          "|---|---|---|---|---|"]
    for q, c in zip(questions, cevaplar):
        L.append(f"| {q['id']} | {q['tur']} | {c['durum']} | {len(c['cumleler'])} / {len(c['cikarilan_cumleler'])} | "
                 + (", ".join(f"{u['kaynak']}:{u['tur']}" for u in c["uyarilar"]) or "—") + " |")
    yorum = ROOT / "evals" / "holdout_yorum.md"
    if yorum.exists():
        L += ["", yorum.read_text(encoding="utf-8")]
    (ROOT / "evals" / "HOLDOUT_RAPOR.md").write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
    print("rapor -> evals/HOLDOUT_RAPOR.md")


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--rapor", action="store_true")
    args = ap.parse_args()
    questions = yaml.safe_load((ROOT / "evals/holdout.yaml").read_text(encoding="utf-8"))["sorular"]
    if not args.rapor:
        if (OUT / "arama_sonuclari.json").exists():
            sys.exit("Holdout zaten koşuldu (evals/holdout_cevaplari/). Yalnız --rapor kullanılabilir.")
        kos(questions)
    rapor(questions)


if __name__ == "__main__":
    main()
