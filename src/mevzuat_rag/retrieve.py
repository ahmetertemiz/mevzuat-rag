"""Arama: yoğun (bge-m3), anahtar kelime (BM25) ve ikisinin Reciprocal Rank Fusion ile birleşimi.

Veri küçük (~200 parça), bu yüzden veritabanı yok: embedding'ler bir numpy dizisinde, benzerlik
düz bir matris çarpımı. Vektörler normalize edildiği için iç çarpım = kosinüs benzerliği.

RRF: her yöntemin sıralamasında parçanın sırası r ise skor = Σ 1 / (RRF_K + r). Ağırlık yok,
ayarlanacak tek sabit literatürdeki standart değer RRF_K = 60. Değerlendirme sonuçlarına göre
değiştirilmez.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from rank_bm25 import BM25Okapi

from . import config
from .textnorm import document_tokens, query_tokens

RRF_K = 60
MODES = ("hybrid", "dense", "bm25")


@dataclass
class Hit:
    rank: int
    score: float
    chunk: dict
    dense_rank: int | None = None
    bm25_rank: int | None = None


def load_chunks(path: Path = config.CHUNKS_PATH) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        chunks = [json.loads(line) for line in f]
    return [c for c in chunks if c["indekse_dahil"]]


def chunks_fingerprint(chunks: list[dict]) -> str:
    h = hashlib.sha256()
    for c in chunks:
        h.update(c["chunk_id"].encode())
        h.update(c["arama_metni"].encode())
    return h.hexdigest()


def bm25_corpus(chunks: list[dict]) -> list[list[str]]:
    out = []
    for c in chunks:
        header = c["baglam_basligi"]
        body = c["arama_metni"][len(header):]
        out.append(document_tokens(header, body))
    return out


def rrf(rankings: list[list[int]], n: int, k: int = RRF_K) -> np.ndarray:
    """rankings: her yöntem için parça indekslerinin en iyiden kötüye sıralı listesi."""
    scores = np.zeros(n)
    for order in rankings:
        for r, idx in enumerate(order, 1):
            scores[idx] += 1.0 / (k + r)
    return scores


class Embedder:
    def __init__(self, model_name: str = config.EMBED_MODEL, max_seq_length: int = config.EMBED_MAX_TOKENS):
        from sentence_transformers import SentenceTransformer  # yavaş import; yalnızca gerekince

        self.model_name = model_name
        try:
            # Model önbellekteyse ağa hiç çıkma (başlangıç süresi ve gizlilik için).
            self.model = SentenceTransformer(model_name, device="cpu", local_files_only=True)
        except OSError:
            self.model = SentenceTransformer(model_name, device="cpu")  # ilk çalıştırma: indir
        self.model.max_seq_length = max_seq_length

    def encode(self, texts: list[str], batch_size: int = 8) -> np.ndarray:
        return self.model.encode(texts, batch_size=batch_size, normalize_embeddings=True,
                                 convert_to_numpy=True, show_progress_bar=False).astype(np.float32)

    def token_lengths(self, texts: list[str]) -> list[int]:
        tok = self.model.tokenizer
        return [len(tok(t, add_special_tokens=True)["input_ids"]) for t in texts]


class Retriever:
    def __init__(self, chunks_path: Path = config.CHUNKS_PATH, index_dir: Path = config.INDEX_DIR,
                 load_model: bool = True):
        self.chunks = load_chunks(chunks_path)
        self.bm25 = BM25Okapi(bm25_corpus(self.chunks))
        self.embedder: Embedder | None = None
        self.emb: np.ndarray | None = None
        if load_model:
            meta = json.loads((index_dir / "meta.json").read_text(encoding="utf-8"))
            if meta["chunks_fingerprint"] != chunks_fingerprint(self.chunks):
                raise RuntimeError("İndeks güncel değil: python scripts/build_index.py çalıştırın.")
            self.emb = np.load(index_dir / "embeddings.npy")
            self.embedder = Embedder(meta["model"], meta["max_seq_length"])

    # -------------------------------------------------- sıralamalar (en iyiden kötüye indeksler)
    def dense_scores(self, query: str) -> np.ndarray:
        if self.embedder is None or self.emb is None:
            raise RuntimeError("Model yüklenmedi (load_model=False).")
        q = self.embedder.encode([query])[0]
        return self.emb @ q

    def bm25_scores(self, query: str) -> np.ndarray:
        return self.bm25.get_scores(query_tokens(query))

    def search(self, query: str, k: int = 5, mode: str = "hybrid") -> list[Hit]:
        if mode not in MODES:
            raise ValueError(f"mode {MODES} içinden olmalı")
        n = len(self.chunks)
        dense_order = bm25_order = None
        if mode in ("dense", "hybrid"):
            ds = self.dense_scores(query)
            dense_order = list(np.argsort(-ds, kind="stable"))
        if mode in ("bm25", "hybrid"):
            bs = self.bm25_scores(query)
            bm25_order = list(np.argsort(-bs, kind="stable"))

        if mode == "dense":
            order, scores = dense_order, ds
        elif mode == "bm25":
            order, scores = bm25_order, bs
        else:
            scores = rrf([dense_order, bm25_order], n)
            order = list(np.argsort(-scores, kind="stable"))

        d_rank = {idx: r for r, idx in enumerate(dense_order, 1)} if dense_order else {}
        b_rank = {idx: r for r, idx in enumerate(bm25_order, 1)} if bm25_order else {}
        return [Hit(rank=r, score=float(scores[i]), chunk=self.chunks[i],
                    dense_rank=d_rank.get(i), bm25_rank=b_rank.get(i))
                for r, i in enumerate(order[:k], 1)]
