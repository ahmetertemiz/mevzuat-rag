"""bge-m3 için bellek ve süre ölçümü (yayın kararı için).

Ölçülenler (temiz bir süreçte):
  - import (torch + sentence-transformers) süresi ve bellek artışı
  - model yükleme süresi (diskteki önbellekten) ve bellek
  - tüm parçaların embedding süresi (indeks kurma) ve tepe bellek
  - sorgu başına süre: sorgu embedding'i, BM25, hibrit arama toplamı (medyan / p95 / en kötü)

Sorgu süresi için evals/retrieval.yaml'daki soru metinleri yalnızca yük olarak kullanılır;
arama sonuçları okunmaz ve yazdırılmaz.

Kullanım:  python scripts/benchmark_model.py
"""
from __future__ import annotations

import os
import platform
import statistics
import sys
import threading
import time
from pathlib import Path

import psutil
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

PROC = psutil.Process()


def rss_mb() -> float:
    return PROC.memory_info().rss / 2**20


class PeakSampler:
    def __init__(self, interval: float = 0.02):
        self.peak = rss_mb()
        self._stop = threading.Event()
        self._t = threading.Thread(target=self._run, args=(interval,), daemon=True)

    def _run(self, interval):
        while not self._stop.is_set():
            self.peak = max(self.peak, rss_mb())
            time.sleep(interval)

    def __enter__(self):
        self._t.start()
        return self

    def __exit__(self, *a):
        self._stop.set()
        self._t.join()
        self.peak = max(self.peak, rss_mb())


def dir_size_mb(p: Path) -> float:
    return sum(f.stat().st_size for f in p.rglob("*") if f.is_file()) / 2**20 if p.exists() else 0.0


def pct(xs, q):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(round(q * (len(xs) - 1))))]


def main() -> None:
    out: dict = {}
    base = rss_mb()
    with PeakSampler() as ps:
        t0 = time.perf_counter()
        import torch  # noqa: F401
        import sentence_transformers  # noqa: F401
        out["import_s"] = time.perf_counter() - t0
    out["import_mb"] = rss_mb() - base
    import torch

    from mevzuat_rag import config
    from mevzuat_rag.retrieve import Embedder, Retriever, load_chunks

    chunks = load_chunks()
    texts = [c["arama_metni"] for c in chunks]

    before = rss_mb()
    with PeakSampler() as ps:
        t0 = time.perf_counter()
        emb = Embedder()
        out["load_s"] = time.perf_counter() - t0
    out["load_mb"] = rss_mb() - before
    out["after_load_rss"] = rss_mb()

    with PeakSampler() as ps:
        t0 = time.perf_counter()
        emb.encode(texts)
        out["encode_all_s"] = time.perf_counter() - t0
    out["encode_peak_rss"] = ps.peak
    out["n_chunks"] = len(texts)

    # sorgu süreleri: aynı süreçte Retriever (modeli yeniden yüklemeden embedder'ı paylaş)
    r = Retriever(load_model=False)
    import json

    import numpy as np
    meta = json.loads((config.INDEX_DIR / "meta.json").read_text(encoding="utf-8"))
    r.emb = np.load(config.INDEX_DIR / "embeddings.npy")
    r.embedder = emb

    qs = [q["soru"] for q in yaml.safe_load((ROOT / "evals/retrieval.yaml").read_text(encoding="utf-8"))["sorular"]]
    for q in qs[:3]:  # ısınma
        r.search(q, mode="hybrid")
    dense_t, bm25_t, hyb_t = [], [], []
    with PeakSampler() as ps:
        for _ in range(3):
            for q in qs:
                t0 = time.perf_counter(); r.dense_scores(q); dense_t.append(time.perf_counter() - t0)
                t0 = time.perf_counter(); r.bm25_scores(q); bm25_t.append(time.perf_counter() - t0)
                t0 = time.perf_counter(); r.search(q, k=5, mode="hybrid"); hyb_t.append(time.perf_counter() - t0)
    out["query_peak_rss"] = ps.peak
    out["final_rss"] = rss_mb()

    hf_cache = Path(os.environ.get("HF_HOME", Path.home() / ".cache" / "huggingface")) / "hub"
    model_dir = next(hf_cache.glob("models--BAAI--bge-m3"), None)
    vm = psutil.virtual_memory()

    def ms(xs):
        return f"{statistics.median(xs)*1000:.0f} / {pct(xs, 0.95)*1000:.0f} / {max(xs)*1000:.0f}"

    lines = [
        "# bge-m3 performans ölçümü\n",
        "`python scripts/benchmark_model.py` ile üretildi. Tek süreç, yalnız CPU.\n",
        "## Ortam\n",
        f"- İşletim sistemi: {platform.platform()}",
        f"- İşlemci: {platform.processor() or 'bilinmiyor'} · mantıksal çekirdek: {os.cpu_count()} · torch iş parçacığı: {torch.get_num_threads()}",
        f"- Toplam RAM: {vm.total / 2**30:.1f} GB",
        f"- Python {platform.python_version()} · torch {torch.__version__} · sentence-transformers {sentence_transformers.__version__}",
        f"- Model: `{meta['model']}` · boyut {meta['dim']} · max_seq_length {meta['max_seq_length']} "
        f"(en uzun parça {meta['max_token_length']} token, kesilen: {meta['truncated'] or 'yok'})",
        f"- Diskteki model önbelleği: {dir_size_mb(model_dir) / 1024:.2f} GB" if model_dir else "- Model önbelleği bulunamadı",
        "",
        "## Bellek (RSS)\n",
        "| Aşama | Değer |",
        "|---|---|",
        f"| Süreç başlangıcı | {base:.0f} MB |",
        f"| torch + sentence-transformers import sonrası artış | +{out['import_mb']:.0f} MB |",
        f"| Model yükleme artışı | +{out['load_mb']:.0f} MB |",
        f"| Model yüklü, boşta | {out['after_load_rss']:.0f} MB |",
        f"| İndeks kurarken tepe ({out['n_chunks']} parça) | {out['encode_peak_rss']:.0f} MB |",
        f"| Sorgu sırasında tepe | {out['query_peak_rss']:.0f} MB |",
        "",
        "## Süreler\n",
        "| Aşama | Süre |",
        "|---|---|",
        f"| import (torch + sentence-transformers) | {out['import_s']:.1f} sn |",
        f"| Model yükleme (önbellekten) | {out['load_s']:.1f} sn |",
        f"| Soğuk başlangıç toplamı (import + yükleme) | {out['import_s'] + out['load_s']:.1f} sn |",
        f"| Tüm parçaların embedding'i ({out['n_chunks']}) | {out['encode_all_s']:.1f} sn "
        f"({out['encode_all_s'] / out['n_chunks'] * 1000:.0f} ms/parça) |",
        "",
        f"Sorgu başına ({len(qs)} soru × 3 tekrar = {len(hyb_t)} ölçüm; medyan / p95 / en kötü):\n",
        "| İşlem | ms |",
        "|---|---|",
        f"| Sorgu embedding'i + benzerlik (dense) | {ms(dense_t)} |",
        f"| BM25 | {ms(bm25_t)} |",
        f"| Hibrit arama toplamı (dense + BM25 + RRF) | {ms(hyb_t)} |",
        "",
        "## Yayın açısından yorum\n",
        "- **Gerçek bellek ihtiyacı \"model yüklü, boşta\" satırı değil, sorgu sırasındaki tepedir.** "
        "Ağırlıklar (safetensors) belleğe eşlenerek açılır ve ilk embedding'de sayfalanır; bu yüzden "
        "yükleme anında RSS düşük görünür, ilk sorgudan sonra model ağırlıklarının tamamı (fp32, ~2,2 GB) "
        "bellektedir. Yayın ortamında süreç başına ~2,5 GB RAM ayrılmalı.",
        "- Sorgu süresinin neredeyse tamamı sorgu embedding'inden gelir; BM25 ve RRF ihmal edilebilir.",
        "- ~200 parçalık indeks (float32, 1024 boyut) yaklaşık 1 MB'tır; indeks yayında yeniden "
        "hesaplanmaz, dosyadan okunur. İndeks kurma (~2 dk) yalnızca belgeler değişince gerekir.",
        "- Diskteki önbellek, Windows'ta sembolik bağlantı kullanılamadığı için dosyaların kopyalanmasından "
        "dolayı model boyutunun yaklaşık iki katıdır; Linux'ta yaklaşık yarısı beklenir.",
        "- Soğuk başlangıç süresi, ücretsiz barındırma ortamlarında (uyku sonrası uyanma) kullanıcının "
        "beklediği süreye doğrudan eklenir.",
    ]
    path = ROOT / "reports" / "performans.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
