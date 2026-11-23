"""Cevap üretimi değerlendirmesi: evals/answers.yaml -> evals/CEVAP_RAPOR.md

Her koşuda arama (yeniden yazım dahil, dondurulmuş varsayılan hat) soru başına BİR kez yapılır;
karşılaştırılan modeller aynı bağlamı görür. Böylece modeller arası fark yalnız cevap üretiminden gelir.

Otomatik ölçütler (soru başına):
  - madde_dogru   : doğrulanmış dayanakların maddeleri her dayanak gereksinimini karşılıyor mu (cevaplı)
  - olgu          : beklenen olgulardan kaçı gösterilen cümlelerde ya da uyarılarda geçiyor (normalleştirilmiş)
  - baglamda      : beklenen maddeler bağlamdaydı mı (arama hatasını üretim hatasından ayırmak için)
  - yanlis_ret    : cevaplı soruda durum "bulunamadi"
  - dogru_ret     : cevapsız soruda durum "bulunamadi"
  - uyari_isabet  : beklenen uyarı türü cevapta var mı
  - alıntı doğrulama oranı, çıkarılan cümle oranı, maliyet, süre
Elle okuma (yanlış bilgi, tavsiye/hüküm, talimat uygulama) evals/cevap_elle_okuma.yaml'dan okunur.

Kullanım:  python scripts/eval_answers.py [--runs 3] [--models claude-haiku-5-5 claude-sonnet-5-5]
           python scripts/eval_answers.py --rapor   # yalnız kayıtlı koşulardan raporu yeniden üret
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

OUT_DIR = ROOT / "evals" / "cevap_kosulari"
MODELS = ("claude-haiku-5-5", "claude-sonnet-5-5")
TUR_AD = {"normal": "Normal", "mulga_iptal": "Mülga/iptal", "ceza": "Ceza tutarı", "cevapsiz": "Cevapsız"}


def madde_key(p: dict) -> str:
    return f"{p['belge_kisa_ad']}:{p['madde_no']}"


def olc(q: dict, c: dict, chunks: dict[str, dict]) -> dict:
    from mevzuat_rag.verify import norm

    gosterilen = c["cumleler"]
    dayanak_maddeleri = {madde_key(chunks[d["parca_id"]]) for cm in gosterilen for d in cm["dayanaklar"]}
    baglam_maddeleri = {madde_key(chunks[i]) for i in c["baglam_parcalari"] if i in chunks}
    metin = norm(" ".join([cm["metin"] for cm in gosterilen] + [u["metin"] for u in c["uyarilar"]]))
    tum_alinti = [d for cm in gosterilen + c["cikarilan_cumleler"] for d in cm["dayanaklar"]]
    cevapli = q["tur"] != "cevapsiz"
    olgu_bulunan = sum(any(norm(x) in metin for x in o) for o in q["olgular"])
    return {
        "id": q["id"], "tur": q["tur"], "durum": c["durum"],
        "madde_dogru": cevapli and all(any(a in dayanak_maddeleri for a in req) for req in q["dayanak"]),
        "baglamda": cevapli and all(any(a in baglam_maddeleri for a in req) for req in q["dayanak"]),
        "olgu_bulunan": olgu_bulunan, "olgu_toplam": len(q["olgular"]),
        "yanlis_ret": cevapli and c["durum"] == "bulunamadi",
        "dogru_ret": (not cevapli) and c["durum"] == "bulunamadi",
        "uyari_isabet": (q.get("beklenen_uyari") in {u["tur"] for u in c["uyarilar"]}) if q.get("beklenen_uyari") else None,
        "alinti_toplam": len(tum_alinti), "alinti_dogru": sum(d["dogrulandi"] for d in tum_alinti),
        "cumle_toplam": len(gosterilen) + len(c["cikarilan_cumleler"]), "cumle_cikarilan": len(c["cikarilan_cumleler"]),
        "uyari_cikarilan": len(c.get("cikarilan_uyarilar") or []),
        "uyari_model_toplam": sum(u.get("kaynak") == "model" for u in c["uyarilar"]) + len(c.get("cikarilan_uyarilar") or []),
        # Bağlam dışı (uydurma) parça kimliği: yeni koşularda doğrudan sayılır; eski koşularda
        # (sayaç eklenmeden önce) alıntı doğrulama nedeninden ("parça bağlamda yok") çıkarılır.
        "dayanak_toplam": c.get("dayanak_sayisi", len(tum_alinti)),
        "baglam_disi": (len(c["baglam_disi_dayanaklar"]) if "baglam_disi_dayanaklar" in c
                        else sum(d.get("neden") == "parça bağlamda yok" for d in tum_alinti)),
        "maliyet": c["maliyet_usd"] - (c["arama"].get("maliyet_usd") or 0.0), "sure": c["sure_sn"],
    }


def kos(runs: int, models: list[str], workers: int) -> None:
    from mevzuat_rag.answer import Cevaplayici, cevap_sozlugu
    from mevzuat_rag.pipeline import Arayici

    questions = yaml.safe_load((ROOT / "evals/answers.yaml").read_text(encoding="utf-8"))["sorular"]
    arayici = Arayici()
    cevaplayicilar = {m: Cevaplayici(arayici=arayici, model=m) for m in models}
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for run in range(1, runs + 1):
        with ThreadPoolExecutor(max_workers=workers) as ex:
            aramalar = list(ex.map(lambda q: arayici.ara(q["soru"], k=cevaplayicilar[models[0]].k), questions))
        for m in models:
            cv = cevaplayicilar[m]
            with ThreadPoolExecutor(max_workers=workers) as ex:
                cevaplar = list(ex.map(lambda qs: cevap_sozlugu(cv.cevapla_aramayla(qs[0]["soru"], qs[1])),
                                       zip(questions, aramalar)))
            for q, c in zip(questions, cevaplar):
                c["id"] = q["id"]
            (OUT_DIR / f"{m}_kosu{run}.json").write_text(
                json.dumps(cevaplar, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
            print(f"{m} koşu {run}: tamam (${sum(c['maliyet_usd'] for c in cevaplar):.4f})")


def ozet(xs) -> str:
    return f"{min(xs):g} / {statistics.median(xs):g} / {max(xs):g}"


def rapor() -> None:
    from mevzuat_rag.retrieve import load_chunks

    questions = yaml.safe_load((ROOT / "evals/answers.yaml").read_text(encoding="utf-8"))["sorular"]
    qmap = {q["id"]: q for q in questions}
    with (ROOT / "data" / "chunks.jsonl").open(encoding="utf-8") as f:
        chunks = {c["chunk_id"]: c for c in map(json.loads, f)}
    _ = load_chunks
    elle = {}
    ep = ROOT / "evals" / "cevap_elle_okuma.yaml"
    if ep.exists():
        elle = yaml.safe_load(ep.read_text(encoding="utf-8")) or {}

    runs: dict[str, list[list[dict]]] = {}
    for f in sorted(OUT_DIR.glob("*_kosu*.json")):
        m = f.name.split("_kosu")[0]
        cevaplar = json.loads(f.read_text(encoding="utf-8"))
        runs.setdefault(m, []).append([olc(qmap[c["id"]], c, chunks) for c in cevaplar])
    models = [m for m in MODELS if m in runs] + [m for m in runs if m not in MODELS]

    ans_ids = [q["id"] for q in questions if q["tur"] != "cevapsiz"]
    una_ids = [q["id"] for q in questions if q["tur"] == "cevapsiz"]
    uy_ids = [q["id"] for q in questions if q.get("beklenen_uyari")]
    L = ["# Cevap üretimi değerlendirmesi\n",
         "`python scripts/eval_answers.py` tarafından üretilir. Set: `evals/answers.yaml` "
         f"({len(questions)} soru: {len(ans_ids)} cevaplı, {len(una_ids)} cevapsız). Arama dondurulmuş "
         "varsayılan hat (BM25 + yeniden yazım, Haiku 5.5, prompt v3), k=8. Her koşuda arama soru başına bir "
         "kez yapıldı; modeller aynı bağlamı gördü. Hücreler: en düşük / medyan / en yüksek (koşular arası).\n"]

    def per_run(m, fn):
        return [fn({r["id"]: r for r in run}) for run in runs[m]]

    rows = [
        ("Yanlış olgu (elle okuma, cevap sayısı)", lambda m: [len(x.get("yanlis_bilgi") or []) for x in (elle.get(m) or {}).values()] or None),
        ("Yanlış reddetme (cevaplı 15'te)", lambda m: per_run(m, lambda d: sum(d[i]["yanlis_ret"] for i in ans_ids))),
        ("Madde doğruluğu (cevaplı 15'te)", lambda m: per_run(m, lambda d: sum(d[i]["madde_dogru"] for i in ans_ids))),
        ("Olgu oranı (%)", lambda m: per_run(m, lambda d: round(100 * sum(d[i]["olgu_bulunan"] for i in ans_ids)
                                                                  / sum(d[i]["olgu_toplam"] for i in ans_ids)))),
        ("Doğru reddetme (cevapsız 5'te)", lambda m: per_run(m, lambda d: sum(d[i]["dogru_ret"] for i in una_ids))),
        ("Uyarı isabeti (beklenen uyarılı 3'te)", lambda m: per_run(m, lambda d: sum(bool(d[i]["uyari_isabet"]) for i in uy_ids))),
        ("Alıntı doğrulama oranı (%)", lambda m: per_run(m, lambda d: round(100 * sum(r["alinti_dogru"] for r in d.values())
                                                                            / max(1, sum(r["alinti_toplam"] for r in d.values()))))),
        ("Çıkarılan cümle oranı (%)", lambda m: per_run(m, lambda d: round(100 * sum(r["cumle_cikarilan"] for r in d.values())
                                                                           / max(1, sum(r["cumle_toplam"] for r in d.values())), 1))),
        ("Çıkarılan cümle içeren cevap", lambda m: per_run(m, lambda d: sum(r["cumle_cikarilan"] > 0 for r in d.values()))),
        ("Bağlam dışı parça kimliği (dayanak sayısı)", lambda m: per_run(m, lambda d: sum(r["baglam_disi"] for r in d.values()))),
        ("Bağlam dışı parça kimliği oranı (%)", lambda m: per_run(m, lambda d: round(100 * sum(r["baglam_disi"] for r in d.values())
                                                                                     / max(1, sum(r["dayanak_toplam"] for r in d.values())), 1))),
        ("Çıkarılan model uyarısı", lambda m: per_run(m, lambda d: sum(r["uyari_cikarilan"] for r in d.values()))),
        ("Maliyet / cevap ($, arama hariç)", lambda m: per_run(m, lambda d: round(statistics.mean(r["maliyet"] for r in d.values()), 5))),
        ("Süre / cevap medyanı (sn, arama dahil)", lambda m: per_run(m, lambda d: round(statistics.median(r["sure"] for r in d.values()), 1))),
        ("Liste eksik aktarılmış (elle okuma)", lambda m: [len(x.get("liste_eksik") or []) for x in (elle.get(m) or {}).values()] or None),
        ("Hüküm / tavsiye (elle okuma)", lambda m: [len(x.get("tavsiye_hukum") or []) for x in (elle.get(m) or {}).values()] or None),
        ("Gömülü talimatı uyguladı (A11, elle)", lambda m: [len(x.get("talimat_uygulandi") or []) for x in (elle.get(m) or {}).values()] or None),
    ]
    L += ["## 1. Özet\n", "| Ölçüt | " + " | ".join(f"`{m}`" for m in models) + " |", "|---|" + "---|" * len(models)]
    for ad, fn in rows:
        cells = []
        for m in models:
            v = fn(m)
            cells.append(ozet(v) if v else "—")
        L.append(f"| {ad} | " + " | ".join(cells) + " |")
    L.append("")
    L.append("Karar kuralı (öncelik sırasıyla): (a) yanlış olgu sayısı, (b) yanlış reddetme, (c) madde "
             "doğruluğu ve olgu oranı, (d) maliyet ve süre. **Gürültü payı (2026-11-23, sonraki ölçümden "
             "önce eklendi):** Sonnet ancak 3 koşunun toplamında yanlış olgu sayısı Haiku'dan en az 2 "
             "daha azsa seçilir; aksi hâlde Haiku.\n")

    # arama ayrıştırması
    L += ["## 2. Arama mı, üretim mi?\n",
          "Cevaplı sorularda beklenen maddelerin bağlamda olup olmadığı (arama aynı olduğu için modeller arasında ortak).\n",
          "| Soru | Bağlamda (koşu sırasıyla) |", "|---|---|"]
    m0 = models[0]
    for i in ans_ids:
        L.append(f"| {i} | " + "".join("✓" if run_i[i]["baglamda"] else "✗"
                                         for run_i in [{r["id"]: r for r in run} for run in runs[m0]]) + " |")
    L.append("")

    # soru bazında
    L += ["## 3. Soru bazında (koşu sırasıyla)\n",
          "Hücre: durum (C=cevaplandı, K=kısmen, B=bulunamadı) · madde ✓/✗ · olgu bulunan/toplam · çıkarılan cümle.\n",
          "| Soru | Tür | " + " | ".join(f"`{m}`" for m in models) + " |", "|---|---|" + "---|" * len(models)]
    kis = {"cevaplandi": "C", "kismen_cevaplandi": "K", "bulunamadi": "B"}
    for q in questions:
        cells = []
        for m in models:
            parts = []
            for run in runs[m]:
                r = next(x for x in run if x["id"] == q["id"])
                s = kis[r["durum"]]
                if q["tur"] != "cevapsiz":
                    s += ("✓" if r["madde_dogru"] else "✗") + f"{r['olgu_bulunan']}/{r['olgu_toplam']}"
                if r["cumle_cikarilan"]:
                    s += f"−{r['cumle_cikarilan']}"
                parts.append(s)
            cells.append(" · ".join(parts))
        L.append(f"| {q['id']} | {TUR_AD[q['tur']]} | " + " | ".join(cells) + " |")
    L.append("")

    if elle:
        L += ["## 4. Elle okuma\n",
              "Her model için üç koşunun 20 cevabının hepsi okundu (`evals/cevap_elle_okuma.yaml`).\n"]
        for m in models:
            for kosu, x in (elle.get(m) or {}).items():
                for alan, ad in (("yanlis_bilgi", "Yanlış bilgi"), ("tavsiye_hukum", "Hüküm/tavsiye"),
                                 ("talimat_uygulandi", "Talimat uygulandı"),
                                 ("liste_eksik", "Liste eksik")):
                    for item in x.get(alan) or []:
                        L.append(f"- `{m}` {kosu} · {ad} · **{item['id']}**: {item['aciklama']}")
        if elle.get("notlar"):
            L += ["", "### Notlar\n"] + [f"- {n}" for n in elle["notlar"]]
        L.append("")
    yorum = ROOT / "evals" / "cevap_yorum.md"
    if yorum.exists():
        L.append(yorum.read_text(encoding="utf-8"))
    out = ROOT / "evals" / "CEVAP_RAPOR.md"
    out.write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
    print(f"rapor -> {out.relative_to(ROOT)}")


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--models", nargs="+", default=list(MODELS))
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--rapor", action="store_true", help="yalnız raporu kayıtlı koşulardan üret")
    args = ap.parse_args()
    if not args.rapor:
        kos(args.runs, args.models, args.workers)
    rapor()


if __name__ == "__main__":
    main()
