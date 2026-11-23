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
from mevzuat_rag.retrieve import Embedder, chunks_fingerprint, load_chunks  # noqa: E402


def main() -> None:
    chunks = load_chunks()
    texts = [c["arama_metni"] for c in chunks]
    emb = Embedder()
    lengths = emb.token_lengths(texts)
    truncated = [c["chunk_id"] for c, n in zip(chunks, lengths) if n > config.EMBED_MAX_TOKENS]
    print(f"{len(chunks)} parça; token uzunluğu en fazla {max(lengths)}, "
          f"sınır {config.EMBED_MAX_TOKENS}; kesilen: {truncated or 'yok'}")
    t0 = time.perf_counter()
    vecs = emb.encode(texts)
    dt = time.perf_counter() - t0
    config.INDEX_DIR.mkdir(exist_ok=True)
    np.save(config.INDEX_DIR / "embeddings.npy", vecs)
    meta = {
        "model": config.EMBED_MODEL,
        "max_seq_length": config.EMBED_MAX_TOKENS,
        "dim": int(vecs.shape[1]),
        "n": len(chunks),
        "chunk_ids": [c["chunk_id"] for c in chunks],
        "chunks_fingerprint": chunks_fingerprint(chunks),
        "max_token_length": max(lengths),
        "truncated": truncated,
        "encode_seconds": round(dt, 2),
        "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    (config.INDEX_DIR / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"embedding: {vecs.shape}, {dt:.1f} sn -> {config.INDEX_DIR.relative_to(config.ROOT)}")


if __name__ == "__main__":
    main()
