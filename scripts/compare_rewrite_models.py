"""Yeniden yazım modeli karşılaştırması: BM25 + yeniden yazım, geliştirme seti.

Her model aynı prompt (rewrite.PROMPT_VERSION), aynı effort ve aynı JSON şemasıyla, ÖNBELLEKSİZ
olarak --runs kez koşulur. Model çıktısı koşudan koşuya değiştiği için sonuçlar aralık
(en düşük–en yüksek) olarak raporlanır.

Bir çağrı hata verirse ya da reddedilirse o soru düz BM25 ile aranır (üretim davranışıyla aynı) ve
raporda sayılır.

Çıktılar: evals/MODEL_KARSILASTIRMA.md, evals/model_karsilastirma/<model>_kosu<n>.json
Holdout setine dokunmaz.

Kullanım:  python scripts/compare_rewrite_models.py [--runs 3] [--workers 4]
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
sys.path.insert(0, str(ROOT / "scripts"))

from eval_retrieval import KS, TUR_AD, ranked_articles  # noqa: E402
from mevzuat_rag.retrieve import Retriever  # noqa: E402
from mevzuat_rag.rewrite import (PROMPT_VERSION, REWRITE_EFFORT, SERVER_FALLBACK_MODELS,  # noqa: E402
                                 QueryRewriter)

MODELS = ("claude-haiku-5-5", "claude-sonnet-5-5", "claude-opus-5-5")
TURLER = ("madde_dili", "gunluk_dil", "iki_madde", "madde_numarasi")
OUT_DIR = ROOT / "evals" / "model_karsilastirma"


def one_call(rw: QueryRewriter, q: dict) -> dict:
    import anthropic
    try:
        r = rw.rewrite(q["soru"])
        rec = asdict(r)
        rec["hata"] = None
        if r.stop_reason == "refusal" or not r.sorgular:
            rec["hata"] = f"sorgu üretilmedi (stop_reason={r.stop_reason})"
    except anthropic.APIError as e:  # bağlantı, zaman aşımı, 4xx/5xx
        rec = {"soru": q["soru"], "sorgular": [], "model": rw.model, "input_tokens": 0,
               "output_tokens": 0, "cost_usd": 0.0, "seconds": None, "stop_reason": "",
               "hata": f"{type(e).__name__}"}
    rec["id"] = q["id"]
    return rec


def score(bm25: Retriever, questions: list[dict], recs: dict[str, dict]) -> list[dict]:
    rows = []
    for q in questions:
        extra = recs[q["id"]]["sorgular"]  # boşsa düz BM25 (üretimdeki düşme davranışı)
        hits = bm25.search(q["soru"], k=len(bm25.chunks), mode="bm25", extra_queries=extra)
        keys = [a for a, _ in ranked_articles(hits)]
        ranks = []
        for req in q["dogru"]:
            rr = [keys.index(a) + 1 for a in req if a in keys]
            ranks.append(min(rr) if rr else None)
        row = {"id": q["id"], "tur": q["tur"], "siralar": ranks}
        for k in KS:
            met = [x is not None and x <= k for x in ranks]
            row[f"@{k}"] = bool(met) and all(met)
        rows.append(row)
    return rows


def rng(xs) -> str:
    lo, hi = min(xs), max(xs)
    return f"{lo}" if lo == hi else f"{lo}–{hi}"


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()

    questions = yaml.safe_load((ROOT / "evals/retrieval.yaml").read_text(encoding="utf-8"))["sorular"]
    bm25 = Retriever(load_model=False)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    all_runs: dict[str, list[dict]] = {}
    for m in MODELS:
        rw = QueryRewriter(model=m)
        all_runs[m] = []
        for run in range(1, args.runs + 1):
            with ThreadPoolExecutor(max_workers=args.workers) as ex:
                recs = list(ex.map(lambda q: one_call(rw, q), questions))
            by_id = {r["id"]: r for r in recs}
            rows = score(bm25, questions, by_id)
            (OUT_DIR / f"{m}_kosu{run}.json").write_text(
                json.dumps({"prompt_surumu": PROMPT_VERSION, "effort": REWRITE_EFFORT, "cagrilar": recs,
                            "sonuclar": rows}, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
            all_runs[m].append({"recs": recs, "rows": rows})
            ans = [r for r in rows if r["tur"] != "cevapsiz"]
            fails = sum(1 for r in recs if r["hata"])
            print(f"{m:18s} koşu {run}: " + "  ".join(f"@{k}={sum(r[f'@{k}'] for r in ans)}" for k in KS)
                  + f"  hata={fails}  ${sum(r['cost_usd'] for r in recs):.4f}")

    # düz BM25 referansı
    plain = score(bm25, questions, {q["id"]: {"sorgular": []} for q in questions})
    (ROOT / "evals" / "MODEL_KARSILASTIRMA.md").write_text(
        render(questions, all_runs, plain, args.runs), encoding="utf-8", newline="\n")
    print("rapor -> evals/MODEL_KARSILASTIRMA.md")


def render(questions, all_runs, plain, n_runs) -> str:
    L: list[str] = []
    w = L.append
    ans_ids = [q["id"] for q in questions if q["tur"] != "cevapsiz"]
    by_type = {t: [q["id"] for q in questions if q["tur"] == t] for t in TURLER}
    w("# Yeniden yazım modeli karşılaştırması (BM25 + yeniden yazım)\n")
    w("`python scripts/compare_rewrite_models.py` tarafından üretilir. Geliştirme seti "
      f"(`evals/retrieval.yaml`, {len(ans_ids)} cevaplı soru). Holdout kullanılmadı.\n")
    w(f"- Prompt sürümü {PROMPT_VERSION} (çok konulu sorularda konu başına en az bir sorgu, en fazla 4), "
      f"effort `{REWRITE_EFFORT}`, JSON şeması; üç modelde aynı.")
    w(f"- Her model **{n_runs} kez, önbelleksiz** koşuldu; hücrelerde koşular arası aralık (en düşük–en yüksek).")
    w(f"- Sunucu tarafı reddetme fallback'i: {', '.join(sorted(SERVER_FALLBACK_MODELS))} (Haiku 5.5'te bu özellik yok).")
    w("- Çağrı hata verir ya da sorgu üretmezse soru düz BM25 ile aranır; \"Hata\" sütunu bunları sayar.")
    w("- Süre: tek çağrının uçtan uca süresi (istemci tarafı, 4 paralel istek). Maliyet: usage token'ları × "
      "liste fiyatı (Haiku 5.5 $0.10/$0.50, Sonnet 5.5 $2/$10, Opus 5.5 $4/$20 / 1M token).\n")

    w("## 1. Ana tablo\n")
    w("| Model | @1 | @3 | @5 | Madde dili @5 | Günlük dil @5 | İki madde @5 | Madde no @5 | Süre medyan / p95 | Maliyet / sorgu | Sorgu sayısı (ort.) | Hata |")
    w("|---|---|---|---|---|---|---|---|---|---|---|---|")
    cells_plain = [str(sum(r[f"@{k}"] for r in plain if r["id"] in ans_ids)) for k in KS]
    pb = {r["id"]: r for r in plain}
    cells_plain += [str(sum(pb[i]["@5"] for i in by_type[t])) for t in TURLER]
    w("| _düz BM25 (referans)_ | " + " | ".join(cells_plain) + " | ~1 ms | $0 | 0 | — |")
    for m, runs in all_runs.items():
        per = [{r["id"]: r for r in run["rows"]} for run in runs]
        cells = [rng([sum(p[i][f"@{k}"] for i in ans_ids) for p in per]) for k in KS]
        cells += [rng([sum(p[i]["@5"] for i in by_type[t]) for p in per]) for t in TURLER]
        secs = [r["seconds"] for run in runs for r in run["recs"] if r["seconds"] is not None]
        secs.sort()
        p95 = secs[min(len(secs) - 1, int(round(0.95 * (len(secs) - 1))))] if secs else 0
        costs = [statistics.mean(r["cost_usd"] for r in run["recs"]) for run in runs]
        nq = statistics.mean(len(r["sorgular"]) for run in runs for r in run["recs"])
        fails = [sum(1 for r in run["recs"] if r["hata"]) for run in runs]
        w(f"| `{m}` | " + " | ".join(cells) +
          f" | {statistics.median(secs):.1f} / {p95:.1f} sn | ${statistics.mean(costs):.5f} | {nq:.1f} | {rng(fails)} |")
    w("")

    w("## 2. Soru türüne göre @1 / @3 / @5 (aralık)\n")
    w("| Model | " + " | ".join(f"{TUR_AD[t]} (n={len(by_type[t])})" for t in TURLER) + " |")
    w("|---|" + "---|" * len(TURLER))
    for m, runs in all_runs.items():
        per = [{r["id"]: r for r in run["rows"]} for run in runs]
        cells = []
        for t in TURLER:
            cells.append(" / ".join(rng([sum(p[i][f"@{k}"] for i in by_type[t]) for p in per]) for k in KS))
        w(f"| `{m}` | " + " | ".join(cells) + " |")
    w("")

    w("## 3. Kararsız sorular\n")
    w("@5 sonucu koşudan koşuya değişen sorular (✓ = ilk 5'te, ✗ = değil, koşu sırasıyla).\n")
    w("| Model | Sorular |")
    w("|---|---|")
    for m, runs in all_runs.items():
        per = [{r["id"]: r for r in run["rows"]} for run in runs]
        unstable = [i for i in ans_ids if len({p[i]["@5"] for p in per}) > 1]
        w(f"| `{m}` | " + (", ".join(f"{i} ({''.join('✓' if p[i]['@5'] else '✗' for p in per)})"
                                     for i in unstable) or "—") + " |")
    w("")

    w("## 4. Her koşuda başarısız sorular (@5)\n")
    w("| Model | Sorular (doğru maddenin sırası, koşu sırasıyla) |")
    w("|---|---|")
    for m, runs in all_runs.items():
        per = [{r["id"]: r for r in run["rows"]} for run in runs]
        always = [i for i in ans_ids if not any(p[i]["@5"] for p in per)]

        def fmt(i):
            def s(p):
                return "/".join("–" if x is None else str(x) for x in p[i]["siralar"])
            return f"{i} ({', '.join(s(p) for p in per)})"
        w(f"| `{m}` | " + (", ".join(fmt(i) for i in always) or "—") + " |")
    w("")

    w("## 5. Örnek çıktılar (koşu 1, iki konulu sorular)\n")
    for qid in ("S16", "S18", "S19", "S20", "S21"):
        q = next(x for x in questions if x["id"] == qid)
        w(f"**{qid}** {q['soru']}\n")
        for m, runs in all_runs.items():
            rec = next(r for r in runs[0]["recs"] if r["id"] == qid)
            w(f"- `{m}`: " + " · ".join(f"`{s}`" for s in rec["sorgular"]))
        w("")
    yorum = ROOT / "evals" / "model_yorum.md"
    if yorum.exists():
        w(yorum.read_text(encoding="utf-8"))
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    main()
