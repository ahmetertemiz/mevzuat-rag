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
    def __init__(self, spec: config.EmbedSpec | str = config.DEFAULT_EMBED):
        from sentence_transformers import SentenceTransformer  # yavaş import; yalnızca gerekince

        self.spec = config.EMBED_MODELS[spec] if isinstance(spec, str) else spec
        kw = {}
        if self.spec.dtype == "float32":
            import torch
            kw["model_kwargs"] = {"dtype": torch.float32}
        try:
            # Model önbellekteyse ağa hiç çıkma (başlangıç süresi ve gizlilik için).
            self.model = SentenceTransformer(self.spec.name, device="cpu", local_files_only=True, **kw)
        except OSError:
            self.model = SentenceTransformer(self.spec.name, device="cpu", **kw)  # ilk çalıştırma: indir
        self.model.max_seq_length = self.spec.max_tokens

    def _encode(self, texts: list[str], batch_size: int = 8) -> np.ndarray:
        return self.model.encode(texts, batch_size=batch_size, normalize_embeddings=True,
                                 convert_to_numpy=True, show_progress_bar=False).astype(np.float32)

    def encode_docs(self, texts: list[str]) -> np.ndarray:
        return self._encode([self.spec.doc_prefix + t for t in texts])

    def encode_queries(self, texts: list[str]) -> np.ndarray:
        return self._encode([self.spec.query_prefix + t for t in texts])

    def token_lengths(self, texts: list[str]) -> list[int]:
        tok = self.model.tokenizer
        return [len(tok(self.spec.doc_prefix + t, add_special_tokens=True)["input_ids"]) for t in texts]


def index_dir_for(key: str) -> Path:
    return config.INDEX_DIR / key


class Retriever:
    def __init__(self, chunks_path: Path = config.CHUNKS_PATH, model: str = config.DEFAULT_EMBED,
                 load_model: bool = True):
        self.chunks = load_chunks(chunks_path)
        self.bm25 = BM25Okapi(bm25_corpus(self.chunks))
        self.embedder: Embedder | None = None
        self.emb: np.ndarray | None = None
        self.model_key = model
        if load_model:
            idx = index_dir_for(model)
            if not (idx / "meta.json").exists():
                raise RuntimeError(f"İndeks yok: python scripts/build_index.py --model {model}")
            meta = json.loads((idx / "meta.json").read_text(encoding="utf-8"))
            if meta["chunks_fingerprint"] != chunks_fingerprint(self.chunks):
                raise RuntimeError(f"İndeks güncel değil: python scripts/build_index.py --model {model}")
            self.emb = np.load(idx / "embeddings.npy")
            self.embedder = Embedder(model)

    # -------------------------------------------------- skorlar
    def dense_scores(self, query: str) -> np.ndarray:
        if self.embedder is None or self.emb is None:
            raise RuntimeError("Model yüklenmedi (load_model=False).")
        return self.emb @ self.embedder.encode_queries([query])[0]

    def bm25_scores(self, query: str) -> np.ndarray:
        return self.bm25.get_scores(query_tokens(query))

    def _orders(self, query: str, mode: str) -> tuple[list[list[int]], dict]:
        """Bir sorgu için yöntemlerin sıralamaları (en iyiden kötüye indeksler) ve ham skorları."""
        orders, raw = [], {}
        if mode in ("dense", "hybrid"):
            raw["dense"] = self.dense_scores(query)
            orders.append(list(np.argsort(-raw["dense"], kind="stable")))
        if mode in ("bm25", "hybrid"):
            raw["bm25"] = self.bm25_scores(query)
            # Yalnızca gerçekten eşleşen parçalar (skor > 0) sıralamaya girer. Skoru 0 olan
            # parçaların "sırası" dosya sırasıdır; RRF'e girerse belgenin ilk maddelerine
            # anlamsız puan verir. BM25 tek başına kullanıldığında eşleşmeyen parça dönmez.
            order = [i for i in np.argsort(-raw["bm25"], kind="stable") if raw["bm25"][i] > 0]
            orders.append(order)
        return orders, raw

    @staticmethod
    def _siralama(scores: np.ndarray) -> list[int]:
        """Skoru sıfırdan büyük indeksler, en iyiden kötüye (skor 0 = hiçbir listede yok)."""
        return [i for i in np.argsort(-scores, kind="stable") if scores[i] > 0]

    def _cesitlendir(self, order: list[int], m: int) -> list[int]:
        say: dict[str, int] = {}
        once, sonra = [], []
        for i in order:
            c = self.chunks[i]
            key = f"{c['belge_kisa_ad']}:{c['madde_no']}"
            if say.get(key, 0) < m:
                say[key] = say.get(key, 0) + 1
                once.append(i)
            else:
                sonra.append(i)
        return once + sonra

    def search(self, query: str, k: int = 5, mode: str = "hybrid",
               extra_queries: list[str] | None = None, birlestirme: str = "duz",
               max_parca_madde: int | None = None) -> list[Hit]:
        """extra_queries verilirse (sorgu yeniden yazımı) özgün sorgu ve ek sorgular ayrı ayrı aranır.

        birlestirme:
          "duz"         : tüm sıralamalar (özgün + her ek sorgu) tek bir ağırlıksız RRF'te birleşir.
          "iki_asamali" : ek sorguların sıralamaları önce kendi aralarında RRF ile birleşir; çıkan tek
                          sıralama özgün sorgunun sıralamasıyla 1:1 RRF'te birleşir. Böylece özgün
                          sorgu, ek sorgu sayısından bağımsız olarak ağırlığın yarısını taşır.
        max_parca_madde: verilirse sonuç listesinde aynı maddeden en fazla bu kadar parça öne alınır;
                         fazlası listenin sonuna (kendi sıralarıyla) ertelenir (parça çeşitliliği)."""
        if mode not in MODES:
            raise ValueError(f"mode {MODES} içinden olmalı")
        if birlestirme not in ("duz", "iki_asamali"):
            raise ValueError("birlestirme 'duz' ya da 'iki_asamali' olmalı")
        n = len(self.chunks)
        orders, raw = self._orders(query, mode)
        ek_orders: list[list[int]] = []
        for q in extra_queries or []:
            ek_orders += self._orders(q, mode)[0]
        if birlestirme == "iki_asamali" and ek_orders:
            ozgun = orders[0] if len(orders) == 1 else self._siralama(rrf(orders, n))
            ek = self._siralama(rrf(ek_orders, n))
            scores = rrf([ozgun, ek], n)
            order = list(np.argsort(-scores, kind="stable"))
        else:
            orders = orders + ek_orders
            if len(orders) == 1:
                scores = raw["dense"] if mode == "dense" else raw["bm25"]
                order = orders[0]
            else:
                scores = rrf(orders, n)
                order = list(np.argsort(-scores, kind="stable"))
        if max_parca_madde:
            order = self._cesitlendir(order, max_parca_madde)
        d_rank = ({i: r for r, i in enumerate(np.argsort(-raw["dense"], kind="stable"), 1)}
                  if "dense" in raw else {})
        b_rank = ({i: r for r, i in enumerate(np.argsort(-raw["bm25"], kind="stable"), 1)}
                  if "bm25" in raw else {})
        return [Hit(rank=r, score=float(scores[i]), chunk=self.chunks[i],
                    dense_rank=d_rank.get(i), bm25_rank=b_rank.get(i))
                for r, i in enumerate(order[:k], 1)]
