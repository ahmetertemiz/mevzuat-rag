"""Geliştirme setinde (evals/retrieval.yaml) yöntem karşılaştırması -> evals/DENEYLER.md

Yapılandırmalar: {BM25, bge-m3, granite-97m, e5-small} × {embedding, hibrit} × {yeniden yazım yok/var}.
Ölçüt eval_retrieval.py ile aynıdır (maddeye indirgenmiş @1/@3/@5; iki maddeli sorularda "tümü").

Model çağrıları:
  - Yeniden yazılmış sorgular evals/cache/rewrites_<model>.json dosyasından okunur.
  - Önbellekte olmayan sorular için model ancak --api verilirse çağrılır (API anahtarı .env'de).
  - --api yoksa ve önbellek eksikse yeniden yazımlı yapılandırmalar atlanır.

Holdout setine (evals/holdout.yaml) dokunmaz.

Kullanım:  python scripts/experiments.py [--api]
"""
from __future__ import annotations

import argparse
import gc
import json
import statistics
import sys
import time
from pathlib import Path

import psutil
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from eval_retrieval import KS, TUR_AD, ranked_articles  # noqa: E402
from mevzuat_rag import config  # noqa: E402
from mevzuat_rag.retrieve import Retriever  # noqa: E402
from mevzuat_rag.rewrite import REWRITE_EFFORT, REWRITE_MODEL, RewriteCache  # noqa: E402

TURLER = ("madde_dili", "gunluk_dil", "iki_madde", "madde_numarasi")
BASELINE = "bge-m3 hibrit"
MODELS = ("bge-m3", "granite-97m", "granite-97m-fp32", "e5-small")
MODE_AD = {"dense": "embedding", "hybrid": "hibrit", "bm25": ""}


def config_name(model: str | None, mode: str, rewrite: bool) -> str:
    base = "BM25" if mode == "bm25" else f"{model} {MODE_AD[mode]}"
    return base + (" + yeniden yazım" if rewrite else "")


def evaluate(search, questions: list[dict]) -> tuple[list[dict], list[float]]:
    rows, times = [], []
    for q in questions:
        t0 = time.perf_counter()
        hits = search(q)
        times.append((time.perf_counter() - t0) * 1000)
        keys = [a for a, _ in ranked_articles(hits)]
        req_ranks = []
        for req in q["dogru"]:
            ranks = [keys.index(a) + 1 for a in req if a in keys]
            req_ranks.append(min(ranks) if ranks else None)
        row = {"id": q["id"], "tur": q["tur"], "siralar": req_ranks, "ilk3": keys[:3]}
        for k in KS:
            met = [rk is not None and rk <= k for rk in req_ranks]
            row[f"@{k}"] = bool(met) and all(met)
        rows.append(row)
    return rows, times


def rss_mb() -> float:
    return psutil.Process().memory_info().rss / 2**20


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--api", action="store_true", help="önbellekte olmayan sorular için model çağrısı yap")
    args = ap.parse_args()

    questions = yaml.safe_load((ROOT / "evals/retrieval.yaml").read_text(encoding="utf-8"))["sorular"]
    cache = RewriteCache(ROOT / "evals" / "cache" / f"rewrites_{REWRITE_MODEL}.json")
    rewriter = None
    if args.api:
        from mevzuat_rag.rewrite import QueryRewriter
        rewriter = QueryRewriter()
    rewrites = {}
    for q in questions:
        try:
            rewrites[q["id"]] = cache.get_or_create(q["soru"], rewriter)
        except KeyError:
            pass
    have_rw = len(rewrites) == len(questions)
    print(f"yeniden yazım: {len(rewrites)}/{len(questions)} soru hazır")

    results: dict[str, dict] = {}

    def run(name, retr, mode, rw, model):
        def search(q):
            extra = rewrites[q["id"]].sorgular if rw else None
            return retr.search(q["soru"], k=len(retr.chunks), mode=mode, extra_queries=extra)
        for q in questions[:2]:  # ısınma
            search(q)
        rows, times = evaluate(search, questions)
        results[name] = {"model": model, "mode": mode, "rewrite": rw, "rows": rows,
                         "search_ms_median": statistics.median(times)}
        ans = [r for r in rows if r["tur"] != "cevapsiz"]
        print(f"{name:38s} " + "  ".join(f"@{k}={sum(r[f'@{k}'] for r in ans)}/{len(ans)}" for k in KS))

    # BM25 (model yüklemeden) ve bellek ölçümü
    r = Retriever(load_model=False)
    bm25_rss = rss_mb()
    run(config_name(None, "bm25", False), r, "bm25", False, None)
    if have_rw:
        run(config_name(None, "bm25", True), r, "bm25", True, None)
    del r
    gc.collect()

    for m in MODELS:
        r = Retriever(model=m)
        for mode in ("dense", "hybrid"):
            run(config_name(m, mode, False), r, mode, False, m)
            if have_rw:
                run(config_name(m, mode, True), r, mode, True, m)
        del r
        gc.collect()

    perf = {}
    for m in MODELS:
        p = ROOT / "reports" / f"performans_{m}.json"
        if p.exists():
            perf[m] = json.loads(p.read_text(encoding="utf-8"))

    rw_cost = statistics.mean(x.cost_usd for x in rewrites.values()) if rewrites else None
    rw_sec = statistics.median(x.seconds for x in rewrites.values()) if rewrites else None
    rw_in = statistics.mean(x.input_tokens for x in rewrites.values()) if rewrites else None
    rw_out = statistics.mean(x.output_tokens for x in rewrites.values()) if rewrites else None

    (ROOT / "evals" / "deneyler.json").write_text(json.dumps(
        {"results": results, "bm25_rss_mb": bm25_rss,
         "rewrite": {"model": REWRITE_MODEL, "effort": REWRITE_EFFORT, "mean_cost_usd": rw_cost,
                     "median_seconds": rw_sec, "mean_input_tokens": rw_in, "mean_output_tokens": rw_out}},
        ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    md = render(results, questions, perf, bm25_rss, rewrites, rw_cost, rw_sec, rw_in, rw_out)
    (ROOT / "evals" / "DENEYLER.md").write_text(md, encoding="utf-8", newline="\n")
    print("rapor -> evals/DENEYLER.md")


def pct(x, n):
    return f"{x}/{n}" if n else "—"


def render(results, questions, perf, bm25_rss, rewrites, rw_cost, rw_sec, rw_in, rw_out) -> str:
    L: list[str] = []
    w = L.append
    ans_ids = [q["id"] for q in questions if q["tur"] != "cevapsiz"]
    by_type = {t: [q["id"] for q in questions if q["tur"] == t] for t in TURLER}
    w("# Yöntem karşılaştırma deneyleri (geliştirme seti)\n")
    w("`python scripts/experiments.py` tarafından üretilir. Soru seti `evals/retrieval.yaml`: "
      f"{len(questions)} soru, {len(ans_ids)} cevaplı (" +
      ", ".join(f"{len(by_type[t])} {TUR_AD[t].lower()}" for t in TURLER) +
      f"), {len(questions) - len(ans_ids)} cevapsız. Holdout seti kullanılmadı.\n")
    w("Bu set seçenekleri karşılaştırmak içindir; seçilen yöntem holdout setinde bir kez doğrulanacak. "
      "Küçük örneklem: cevaplı 26 soruda bir soru yaklaşık 4 puan.\n")
    if rewrites:
        w(f"**Sorgu yeniden yazımı:** `{REWRITE_MODEL}`, effort `{REWRITE_EFFORT}`, yapılandırılmış JSON çıktı; "
          "model soruyu cevaplamadan 2-3 sorgu üretir. Özgün soru ve üretilen sorgular ayrı ayrı aranır, "
          "tüm sıralamalar ağırlıksız RRF (k=60) ile birleştirilir. Prompt'taki örnekler geliştirme "
          "setinden değil, uydurma (`src/mevzuat_rag/rewrite.py`). Ortalama "
          f"{rw_in:.0f} girdi / {rw_out:.0f} çıktı token'ı (çıktıya düşünme token'ları dahil).\n")

    def lat(name, res):
        base = res["search_ms_median"]
        if res["rewrite"] and rw_sec is not None:
            return f"{base:.0f} ms + {rw_sec * 1000:.0f} ms çağrı"
        return f"{base:.0f} ms"

    def mem(res):
        if res["model"] is None:
            return f"~{bm25_rss:.0f} MB"
        p = perf.get(res["model"])
        return f"{p['query_peak_rss']:.0f} MB" if p else "ölçülmedi"

    # 1) ana tablo
    w("## 1. Ana tablo\n")
    w("@k: doğru madde(ler) maddeye indirgenmiş ilk k sonuçta (cevaplı 26 soru). Türe göre sütunlar @5. "
      "Bellek: yayın senaryosunda sorgu sırasındaki tepe RSS (`reports/performans_<model>.json`). "
      "Süre: soru başına arama medyanı (embedding + BM25 + RRF, özgün ve ek sorgular dahil) + varsa model "
      "çağrısının medyan süresi.\n")
    w("| Yöntem | @1 | @3 | @5 | Madde dili @5 | Günlük dil @5 | İki madde @5 | Madde no @5 | Bellek | Sorgu süresi | Model çağrısı / sorgu | Maliyet / sorgu |")
    w("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for name, res in results.items():
        rows = {r["id"]: r for r in res["rows"]}
        cells = [pct(sum(rows[i][f"@{k}"] for i in ans_ids), len(ans_ids)) for k in KS]
        cells += [pct(sum(rows[i]["@5"] for i in by_type[t]), len(by_type[t])) for t in TURLER]
        call = "1" if res["rewrite"] else "0"
        cost = f"${rw_cost:.4f}" if res["rewrite"] and rw_cost is not None else "$0"
        bold = "**" if name == BASELINE else ""
        w(f"| {bold}{name}{bold} | " + " | ".join(cells) + f" | {mem(res)} | {lat(name, res)} | {call} | {cost} |")
    w("")
    w(f"Kalın satır taban çizgisi (şu anki varsayılan). BM25 belleği: torch yüklenmeden süreç RSS'i.\n")

    # 2) türe göre @1/@3/@5
    w("## 2. Soru türüne göre @1 / @3 / @5\n")
    w("| Yöntem | " + " | ".join(TUR_AD[t] for t in TURLER) + " |")
    w("|---|" + "---|" * len(TURLER))
    for name, res in results.items():
        rows = {r["id"]: r for r in res["rows"]}
        cells = []
        for t in TURLER:
            ids = by_type[t]
            cells.append(" / ".join(str(sum(rows[i][f"@{k}"] for i in ids)) for k in KS) + f" (n={len(ids)})")
        w(f"| {name} | " + " | ".join(cells) + " |")
    w("")

    # 3) taban çizgisine göre kazanılan / kaybedilen
    base = {r["id"]: r for r in results[BASELINE]["rows"]}
    w(f"## 3. Taban çizgisine ({BASELINE}) göre kazandırılan ve kaybettirilen sorular\n")
    w("Kazanç: tabanda başarısız, bu yöntemde başarılı; kayıp: tersi. Parantez içinde doğru maddenin "
      "taban → bu yöntem sırası (iki maddeli sorularda en kötü gereksinim).\n")
    w("| Yöntem | @5 kazanç | @5 kayıp | @1 kazanç | @1 kayıp |")
    w("|---|---|---|---|---|")

    def worst(r):
        return "yok" if any(x is None for x in r["siralar"]) else str(max(r["siralar"]))

    for name, res in results.items():
        if name == BASELINE:
            continue
        rows = {r["id"]: r for r in res["rows"]}
        cells = []
        for k in (5, 1):
            gain = [i for i in ans_ids if rows[i][f"@{k}"] and not base[i][f"@{k}"]]
            loss = [i for i in ans_ids if not rows[i][f"@{k}"] and base[i][f"@{k}"]]
            cells.append(", ".join(f"{i} ({worst(base[i])}→{worst(rows[i])})" for i in gain) or "—")
            cells.append(", ".join(f"{i} ({worst(base[i])}→{worst(rows[i])})" for i in loss) or "—")
        w(f"| {name} | " + " | ".join(cells) + " |")
    w("")

    # 4) yeniden yazımın kendi etkisi
    if any(res["rewrite"] for res in results.values()):
        w("## 4. Yeniden yazımın etkisi (aynı model ve mod, yazımsız → yazımlı)\n")
        w("| Yöntem | @5 kazanç | @5 kayıp | @1 kazanç | @1 kayıp |")
        w("|---|---|---|---|---|")
        for name, res in results.items():
            if not res["rewrite"]:
                continue
            plain = {r["id"]: r for r in results[name.replace(" + yeniden yazım", "")]["rows"]}
            rows = {r["id"]: r for r in res["rows"]}
            cells = []
            for k in (5, 1):
                gain = [i for i in ans_ids if rows[i][f"@{k}"] and not plain[i][f"@{k}"]]
                loss = [i for i in ans_ids if not rows[i][f"@{k}"] and plain[i][f"@{k}"]]
                cells.append(", ".join(f"{i} ({worst(plain[i])}→{worst(rows[i])})" for i in gain) or "—")
                cells.append(", ".join(f"{i} ({worst(plain[i])}→{worst(rows[i])})" for i in loss) or "—")
            w(f"| {name.replace(' + yeniden yazım', '')} | " + " | ".join(cells) + " |")
        w("")

    # 5) soru bazında sıralar
    w("## 5. Soru bazında doğru maddenin sırası\n")
    w("Her hücre: gereksinim(ler)in maddeye indirgenmiş listedeki sırası (`–` = ilk 30'da yok).\n")
    names = list(results)
    w("| Soru | Tür | " + " | ".join(names) + " |")
    w("|---|---|" + "---|" * len(names))
    for q in questions:
        if q["tur"] == "cevapsiz":
            continue
        cells = []
        for n in names:
            r = next(x for x in results[n]["rows"] if x["id"] == q["id"])
            cells.append(",".join("–" if (s is None or s > 30) else str(s) for s in r["siralar"]))
        w(f"| {q['id']} | {TUR_AD[q['tur']]} | " + " | ".join(cells) + " |")
    w("")

    # 6) üretilen sorgular
    if rewrites:
        w("## 6. Üretilen sorgular\n")
        for q in questions:
            rw = rewrites.get(q["id"])
            if rw:
                w(f"- **{q['id']}** {q['soru']}  \n  → " + " · ".join(f"`{s}`" for s in rw.sorgular)
                  + (f" _(stop_reason: {rw.stop_reason})_" if rw.stop_reason not in ("end_turn", "") else ""))
        w("")
    yorum = ROOT / "evals" / "deney_yorum.md"
    if yorum.exists():
        w(yorum.read_text(encoding="utf-8"))
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    main()
