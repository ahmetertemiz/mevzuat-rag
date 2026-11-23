"""Arama değerlendirmesi: evals/retrieval.yaml -> evals/RAPOR.md + evals/sonuclar.json

Ölçüt: doğru madde ilk 1 / 3 / 5 SONUÇ MADDESİ içinde mi.
  - Arama parça döndürür; aynı maddenin birden çok parçası tek madde sayılır (sıra korunarak
    maddeye indirgenir). Böylece bölünmüş uzun maddeler kendi kendini itip başka maddeye yer
    kaybettirmez ve "ilk 5" gerçekten 5 farklı madde demektir.
  - Bir gereksinim, alternatiflerinden herhangi biri ilk k'da ise karşılanır.
  - iki_madde sorularında iki ölçü raporlanır: "tümü" (iki gereksinim de ilk k'da) ve
    "en az biri". Genel tabloda "tümü" kullanılır.
  - cevapsiz sorularında isabet ölçülemez; yalnızca ilk sonucun skoru raporlanır ve cevaplı
    soruların ilk sonuç skorlarıyla karşılaştırılır. Eşik konmaz.

Bu betik hiçbir şeyi ayarlamaz. Başarısız soruların sınıflandırması evals/siniflandirma.yaml'dan
(sonuçlara bakılarak elle yazılır) okunup rapora eklenir.

Kullanım:  python scripts/eval_retrieval.py [--set evals/retrieval.yaml]
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mevzuat_rag.retrieve import MODES, Retriever  # noqa: E402

KS = (1, 3, 5)
TURLER = ("madde_dili", "gunluk_dil", "iki_madde", "madde_numarasi")
TUR_AD = {"madde_dili": "Madde dili", "madde_numarasi": "Madde numarası", "gunluk_dil": "Günlük dil", "iki_madde": "İki madde", "cevapsiz": "Cevapsız"}
MODE_AD = {"dense": "Yalnız embedding", "bm25": "Yalnız BM25", "hybrid": "Hibrit (RRF)"}


def article_key(c: dict) -> str:
    return f"{c['belge_kisa_ad']}:{c['madde_no']}"


def ranked_articles(hits) -> list[tuple[str, float]]:
    seen, out = set(), []
    for h in hits:
        key = article_key(h.chunk)
        if key not in seen:
            seen.add(key)
            out.append((key, h.score))
    return out


def evaluate(r: Retriever, questions: list[dict]) -> dict:
    n = len(r.chunks)
    res = {}
    for mode in MODES:
        rows = []
        for q in questions:
            hits = r.search(q["soru"], k=n, mode=mode)
            arts = ranked_articles(hits)
            keys = [a for a, _ in arts]
            req_ranks = []
            for req in q["dogru"]:
                ranks = [keys.index(a) + 1 for a in req if a in keys]
                req_ranks.append(min(ranks) if ranks else None)
            row = {"id": q["id"], "tur": q["tur"], "soru": q["soru"], "dogru": q["dogru"],
                   "gereksinim_siralari": req_ranks, "ilk5": arts[:5], "ilk_skor": arts[0][1]}
            for k in KS:
                met = [rk is not None and rk <= k for rk in req_ranks]
                row[f"tumu@{k}"] = bool(met) and all(met)
                row[f"biri@{k}"] = any(met)
            rows.append(row)
        res[mode] = rows
    return res


def pct(x: int, n: int) -> str:
    return f"{x}/{n} ({100 * x / n:.0f}%)" if n else "—"


def render(res: dict, questions: list[dict], cls: dict) -> str:
    L: list[str] = []
    w = L.append
    answerable = [q for q in questions if q["tur"] != "cevapsiz"]
    w("# Arama değerlendirme raporu\n")
    w("`python scripts/eval_retrieval.py` tarafından üretilir. Soru seti: `evals/retrieval.yaml` "
      f"({len(questions)} soru: " + ", ".join(
          f"{sum(q['tur'] == t for q in questions)} {TUR_AD[t].lower()}" for t in (*TURLER, "cevapsiz")) + ").\n")
    w("**Bu sonuçlara göre hiçbir ayar yapılmadı.** Model, parça sınırı, tokenizer, durak kelimeler "
      "ve RRF sabiti sorular yazılmadan önce belirlendi.\n")
    w("Ölçüt: doğru madde, maddeye indirgenmiş sonuç listesinin ilk 1 / 3 / 5'inde mi. "
      "İki maddeli sorularda genel tabloda iki gereksinimin de karşılanması (\"tümü\") aranır.\n")

    # genel tablo
    w(f"## 1. Genel sonuç (cevaplı {len(answerable)} soru)\n")
    w("| Yöntem | @1 | @3 | @5 |")
    w("|---|---|---|---|")
    for mode in MODES:
        rows = [x for x in res[mode] if x["tur"] != "cevapsiz"]
        w(f"| {MODE_AD[mode]} | " + " | ".join(pct(sum(x[f'tumu@{k}'] for x in rows), len(rows)) for k in KS) + " |")
    w("")

    # tür bazında
    w("## 2. Soru türüne göre\n")
    for t in TURLER:
        w(f"### {TUR_AD[t]}\n")
        if t == "iki_madde":
            w("| Yöntem | tümü @1 | tümü @3 | tümü @5 | en az biri @1 | en az biri @3 | en az biri @5 |")
            w("|---|---|---|---|---|---|---|")
        else:
            w("| Yöntem | @1 | @3 | @5 |")
            w("|---|---|---|---|")
        for mode in MODES:
            rows = [x for x in res[mode] if x["tur"] == t]
            cells = [pct(sum(x[f'tumu@{k}'] for x in rows), len(rows)) for k in KS]
            if t == "iki_madde":
                cells += [pct(sum(x[f'biri@{k}'] for x in rows), len(rows)) for k in KS]
            w(f"| {MODE_AD[mode]} | " + " | ".join(cells) + " |")
        w("")
    w("*İki madde, @1:* tek sonuçta iki ayrı madde bulunamayacağı için \"tümü @1\" bu türde "
      "tanım gereği 0'dır.\n")

    # cevapsız
    w("## 3. Cevabı olmayan sorular\n")
    w("İsabet ölçülemez. İlk sonucun skoru, cevaplı soruların ilk sonuç skorlarıyla karşılaştırıldı. "
      "Skor ölçekleri yöntemler arasında farklıdır (embedding: kosinüs, BM25: ham skor, hibrit: RRF).\n")
    w("| Yöntem | Cevaplı sorularda ilk skor (en düşük / medyan) | " +
      " | ".join(q["id"] for q in questions if q["tur"] == "cevapsiz") + " |")
    w("|---|---|" + "---|" * sum(q["tur"] == "cevapsiz" for q in questions))
    for mode in MODES:
        ans = [x["ilk_skor"] for x in res[mode] if x["tur"] != "cevapsiz"]
        una = [x for x in res[mode] if x["tur"] == "cevapsiz"]
        below = sum(x["ilk_skor"] < min(ans) for x in una)
        w(f"| {MODE_AD[mode]} | {min(ans):.3f} / {statistics.median(ans):.3f} | " +
          " | ".join(f"{x['ilk_skor']:.3f}" for x in una) + " |")
        res.setdefault("_ayrisma", {})[mode] = below
    w("")
    for mode in MODES:
        w(f"- {MODE_AD[mode]}: cevapsız soruların {res['_ayrisma'][mode]}/"
          f"{sum(q['tur'] == 'cevapsiz' for q in questions)} tanesinin ilk skoru, cevaplı soruların en "
          "düşük ilk skorunun altında.")
    w("\nCevapsız soruların ilk sonuçları (hibrit):\n")
    for x in res["hybrid"]:
        if x["tur"] == "cevapsiz":
            w(f"- **{x['id']}** \"{x['soru']}\" → " + ", ".join(f"`{a}`" for a, _ in x["ilk5"][:3]))
    w("")

    # soru bazında tablo
    w("## 4. Soru bazında sonuçlar\n")
    w("Hücrelerde doğru maddenin (her gereksinim için) maddeye indirgenmiş listedeki sırası. "
      "`—` ilk 5'te yok anlamına gelir; parantez içinde tam sıra.\n")
    w("| Soru | Tür | Doğru | " + " | ".join(MODE_AD[m] for m in MODES) + " |")
    w("|---|---|---|---|---|---|")
    for i, q in enumerate(questions):
        if q["tur"] == "cevapsiz":
            continue
        cells = []
        for mode in MODES:
            rk = res[mode][i]["gereksinim_siralari"]
            cells.append(", ".join(("—" if (x is None or x > 5) else str(x)) +
                                   (f" ({x})" if x is not None and x > 5 else "") for x in rk))
        dogru = " + ".join("/".join(req) for req in q["dogru"])
        w(f"| {q['id']} | {TUR_AD[q['tur']]} | {dogru} | " + " | ".join(cells) + " |")
    w("")

    # başarısızlıklar
    w("## 5. Başarısız sorular ve nedenleri\n")
    w("Başarısız: ilgili yöntemde doğru madde(ler) ilk 5'te yok (iki maddeli sorularda: iki "
      "gereksinimden en az biri yok). Nedenler sonuçlara bakılarak elle sınıflandırıldı "
      "(`evals/siniflandirma.yaml`).\n")
    cats = cls.get("kategoriler", {})
    if cats:
        w("Kategoriler:\n")
        for k, v in cats.items():
            w(f"- `{k}`: {v}")
        w("")
    counts: dict = {}
    for mode in MODES:
        fails = [x for x in res[mode] if x["tur"] != "cevapsiz" and not x["tumu@5"]]
        w(f"### {MODE_AD[mode]}: {len(fails)} başarısız\n")
        if not fails:
            continue
        w("| Soru | Doğru (sıra) | İlk 3 sonuç | Neden |")
        w("|---|---|---|---|")
        for x in fails:
            c = cls.get("sorular", {}).get(x["id"], {}).get(mode, {})
            kat = c.get("kategori", "sınıflandırılmadı")
            counts.setdefault(mode, {}).setdefault(kat, 0)
            counts[mode][kat] += 1
            dogru = " + ".join(f"{'/'.join(req)} ({rk if rk else 'yok'})"
                               for req, rk in zip(x["dogru"], x["gereksinim_siralari"]))
            top = ", ".join(f"`{a}`" for a, _ in x["ilk5"][:3])
            w(f"| {x['id']} | {dogru} | {top} | `{kat}`: {c.get('aciklama', '')} |")
        w("")
    if counts:
        w("### Neden dağılımı\n")
        allk = sorted({k for m in counts.values() for k in m})
        w("| Neden | " + " | ".join(MODE_AD[m] for m in MODES) + " |")
        w("|---|---|---|---|")
        for k in allk:
            w(f"| `{k}` | " + " | ".join(str(counts.get(m, {}).get(k, 0)) for m in MODES) + " |")
        w("")
    if cls.get("genel_notlar"):
        w("## 6. Genel gözlemler\n")
        for n in cls["genel_notlar"]:
            w(f"- {n}")
        w("")
    return "\n".join(L) + "\n"


def _run_default(arayici, questions: list[dict]) -> list[dict]:
    n = len(arayici.retriever.chunks)
    rows = []
    for q in questions:
        s = arayici.ara(q["soru"], k=n)
        keys = [k for k, _ in ranked_articles(s.hits)]
        ranks = []
        for req in q["dogru"]:
            rr = [keys.index(x) + 1 for x in req if x in keys]
            ranks.append(min(rr) if rr else None)
        row = {"id": q["id"], "tur": q["tur"], "soru": q["soru"], "siralar": ranks, "ilk5": keys[:5],
               "yeniden_yazim": s.yeniden_yazim, "sorgular": s.sorgular, "uyari": s.uyari,
               "atilan_sorgular": s.atilan_sorgular, "maliyet_usd": s.maliyet_usd,
               "sure_sn": s.yeniden_yazim_sn}
        for k in KS:
            met = [x is not None and x <= k for x in ranks]
            row[f"@{k}"] = bool(met) and all(met)
        rows.append(row)
    return rows


def _ozet(vals: list[int]) -> str:
    """en düşük / medyan / en yüksek"""
    return f"{min(vals)} / {statistics.median(vals):g} / {max(vals)}"


def evaluate_default(questions: list[dict], stem: str, runs: int = 1, arayici=None,
                     out_dir: Path | None = None) -> dict:
    """Varsayılan hattı (pipeline.Arayici) olduğu gibi ölçer: önbellek yok, her soru için canlı
    yeniden yazım çağrısı; çağrı başarısız olursa üretimdeki gibi düz BM25. Model çıktısı koşudan
    koşuya değiştiği için `runs` kez koşulur; en düşük, medyan ve en yüksek raporlanır."""
    from mevzuat_rag import config
    from mevzuat_rag.pipeline import Arayici
    from mevzuat_rag.rewrite import PROMPT_VERSION, REWRITE_MODEL

    out_dir = out_dir or (ROOT / "evals")
    a = arayici or Arayici()
    all_rows = []
    for i in range(1, runs + 1):
        rows = _run_default(a, questions)
        all_rows.append(rows)
        ans = [r for r in rows if r["tur"] != "cevapsiz"]
        print(f"koşu {i}: " + "  ".join(f"@{k}={sum(r[f'@{k}'] for r in ans)}/{len(ans)}" for k in KS)
              + f"  başarısız yazım={sum(r['yeniden_yazim'] != 'uygulandı' for r in rows)}")

    ans_ids = [q["id"] for q in questions if q["tur"] != "cevapsiz"]
    turler = [t for t in ("madde_dili", "gunluk_dil", "iki_madde", "madde_numarasi")
              if any(q["tur"] == t for q in questions)]
    per = [{r["id"]: r for r in rows} for rows in all_rows]

    def count(p, ids, k):
        return sum(p[i][f"@{k}"] for i in ids)

    summary = {f"@{k}": [count(p, ans_ids, k) for p in per] for k in KS}
    L = [f"# Varsayılan hat değerlendirmesi: {stem}\n",
         f"`python scripts/eval_retrieval.py --set evals/{stem}.yaml --varsayilan --runs {runs}` ile üretildi. "
         f"Hat: `{config.DEFAULT_SEARCH_MODE}` + yeniden yazım (`{REWRITE_MODEL}`, prompt v{PROMPT_VERSION}), "
         f"önbelleksiz, **{runs} koşu**. Cevaplı soru: {len(ans_ids)}.\n",
         "## Özet (en düşük / medyan / en yüksek)\n",
         "| | @1 | @3 | @5 |", "|---|---|---|---|",
         f"| Cevaplı {len(ans_ids)} soru | " + " | ".join(_ozet(summary[f'@{k}']) for k in KS) + " |"]
    for t in turler:
        ids = [q["id"] for q in questions if q["tur"] == t]
        L.append(f"| {TUR_AD[t]} (n={len(ids)}) | "
                 + " | ".join(_ozet([count(p, ids, k) for p in per]) for k in KS) + " |")
    L += ["", "## Koşular\n",
          "| Koşu | @1 | @3 | @5 | Başarısız yazım | Atılan sorgu | Maliyet | Yazım süresi medyanı |",
          "|---|---|---|---|---|---|---|---|"]
    for i, rows in enumerate(all_rows, 1):
        p = per[i - 1]
        secs = [r["sure_sn"] for r in rows if r["sure_sn"] is not None]
        L.append(f"| {i} | " + " | ".join(str(count(p, ans_ids, k)) for k in KS)
                 + f" | {sum(r['yeniden_yazim'] != 'uygulandı' for r in rows)}"
                 + f" | {sum(len(r['atilan_sorgular']) for r in rows)}"
                 + f" | ${sum(r['maliyet_usd'] for r in rows):.4f}"
                 + f" | {(statistics.median(secs) if secs else 0):.1f} sn |")
    L += ["", "## Soru bazında doğru maddenin sırası (koşu sırasıyla)\n",
          "| Soru | Tür | Sıralar | @5 |", "|---|---|---|---|"]
    for q in questions:
        if q["tur"] == "cevapsiz":
            continue
        cells = ["/".join("–" if x is None else str(x) for x in p[q["id"]]["siralar"]) for p in per]
        L.append(f"| {q['id']} | {TUR_AD[q['tur']]} | {', '.join(cells)} | "
                 + "".join("✓" if p[q["id"]]["@5"] else "✗" for p in per) + " |")
    L += ["", "## Koşu 1: üretilen sorgular ve uyarılar\n",
          "| Soru | Sorgular / uyarı | Atılan |", "|---|---|---|"]
    for r in all_rows[0]:
        note = " · ".join(f"`{x}`" for x in r["sorgular"]) or (r["uyari"] or "")
        dropped = "; ".join(f"`{d['sorgu']}` ({d['neden']})" for d in r["atilan_sorgular"])
        L.append(f"| {r['id']} | {note} | {dropped} |")
    out = out_dir / f"RAPOR_{stem}_varsayilan.md"
    out.write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
    (out_dir / f"sonuclar_{stem}_varsayilan.json").write_text(
        json.dumps({"kosular": all_rows, "ozet": summary}, ensure_ascii=False, indent=1),
        encoding="utf-8", newline="\n")
    print(f"rapor -> {out}")
    print("özet (en düşük / medyan / en yüksek): "
          + "  ".join(f"@{k}={_ozet(summary[f'@{k}'])}" for k in KS))
    return summary


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", default="evals/retrieval.yaml")
    ap.add_argument("--varsayilan", action="store_true",
                    help="yalnızca varsayılan hattı (BM25 + yeniden yazım, canlı model çağrısı) ölç")
    ap.add_argument("--runs", type=int, default=1,
                    help="--varsayilan için koşu sayısı; en düşük, medyan ve en yüksek raporlanır")
    args = ap.parse_args()
    qpath = ROOT / args.set
    questions = yaml.safe_load(qpath.read_text(encoding="utf-8"))["sorular"]
    if not questions:
        sys.exit(f"{args.set} boş.")
    if args.varsayilan:
        evaluate_default(questions, qpath.stem, runs=args.runs)
        return
    r = Retriever()
    res = evaluate(r, questions)
    stem = qpath.stem
    (ROOT / "evals" / f"sonuclar_{stem}.json").write_text(
        json.dumps({m: res[m] for m in MODES}, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    cls_path = ROOT / "evals" / "siniflandirma.yaml"
    cls = yaml.safe_load(cls_path.read_text(encoding="utf-8")) if cls_path.exists() and stem == "retrieval" else {}
    out = ROOT / "evals" / ("RAPOR.md" if stem == "retrieval" else f"RAPOR_{stem}.md")
    out.write_text(render(res, questions, cls or {}), encoding="utf-8", newline="\n")
    print(f"rapor -> {out.relative_to(ROOT)}")
    for mode in MODES:
        rows = [x for x in res[mode] if x["tur"] != "cevapsiz"]
        print(f"{mode:7s} " + "  ".join(f"@{k}={sum(x[f'tumu@{k}'] for x in rows)}/{len(rows)}" for k in KS))


if __name__ == "__main__":
    main()
