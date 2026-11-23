"""data/chunks.jsonl -> index/embeddings.npy + index/meta.json

Kullanım:  python scripts/build_index.py
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mevzuat_rag import config  # noqa: E402
from mevzuat_rag.retrieve import Embedder, chunks_fingerprint, index_dir_for, load_chunks  # noqa: E402
import argparse  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", choices=list(config.EMBED_MODELS), default=config.DEFAULT_EMBED)
    args = ap.parse_args()
    spec = config.EMBED_MODELS[args.model]
    chunks = load_chunks()
    texts = [c["arama_metni"] for c in chunks]
    emb = Embedder(spec)
    lengths = emb.token_lengths(texts)
    truncated = [c["chunk_id"] for c, n in zip(chunks, lengths) if n > spec.max_tokens]
    print(f"[{spec.key}] {len(chunks)} parça; token uzunluğu en fazla {max(lengths)}, "
          f"sınır {spec.max_tokens}; kesilen ({len(truncated)}): {truncated or 'yok'}")
    t0 = time.perf_counter()
    vecs = emb.encode_docs(texts)
    dt = time.perf_counter() - t0
    out = index_dir_for(spec.key)
    out.mkdir(parents=True, exist_ok=True)
    np.save(out / "embeddings.npy", vecs)
    meta = {
        "model": spec.name,
        "key": spec.key,
        "max_seq_length": spec.max_tokens,
        "dim": int(vecs.shape[1]),
        "n": len(chunks),
        "chunk_ids": [c["chunk_id"] for c in chunks],
        "chunks_fingerprint": chunks_fingerprint(chunks),
        "max_token_length": max(lengths),
        "truncated": truncated,
        "encode_seconds": round(dt, 2),
        "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    (out / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"embedding: {vecs.shape}, {dt:.1f} sn -> {out.relative_to(config.ROOT)}")


if __name__ == "__main__":
    main()
