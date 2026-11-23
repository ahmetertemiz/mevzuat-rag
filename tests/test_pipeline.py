"""Varsayılan hat: BM25 + yeniden yazım ve düşme davranışı. Model çağrısı yapılmaz (sahte yazıcı)."""
import pytest

from mevzuat_rag import config
from mevzuat_rag.pipeline import BASARISIZ, KAPALI, UYGULANDI, Arayici
from mevzuat_rag.retrieve import Retriever
from mevzuat_rag.rewrite import Rewrite


@pytest.fixture(scope="module")
def bm25():
    return Retriever(load_model=False)


class FakeRewriter:
    def __init__(self, sorgular=None, exc=None, stop="end_turn"):
        self.sorgular, self.exc, self.stop = sorgular or [], exc, stop

    def rewrite(self, q):
        if self.exc:
            raise self.exc
        return Rewrite(q, self.sorgular, "sahte", 10, 5, 0.001, 0.1, self.stop)


def test_varsayilan_bm25_ve_yeniden_yazim():
    assert config.DEFAULT_SEARCH_MODE == "bm25"
    assert config.DEFAULT_REWRITE is True


def test_yeniden_yazim_uygulanir(bm25):
    a = Arayici(retriever=bm25, rewriter=FakeRewriter(["mesafeli sözleşmelerde cayma hakkı"]))
    s = a.ara("ayakkabıyı beğenmedim geri verebilir miyim")
    assert s.yeniden_yazim == UYGULANDI and s.uyari is None
    assert s.sorgular == ["mesafeli sözleşmelerde cayma hakkı"]
    assert s.mode == "bm25" and s.hits


@pytest.mark.parametrize("rw", [
    FakeRewriter(exc=TimeoutError("zaman aşımı")),
    FakeRewriter(exc=RuntimeError("API hatası")),
    FakeRewriter(sorgular=[], stop="refusal"),
])
def test_basarisiz_yazim_duz_bm25e_duser(bm25, rw):
    soru = "6502 m.48"
    s = Arayici(retriever=bm25, rewriter=rw).ara(soru, k=3)
    assert s.yeniden_yazim == BASARISIZ
    assert s.uyari and "düz arama yapıldı" in s.uyari
    duz = bm25.search(soru, k=3, mode="bm25")
    assert [h.chunk["chunk_id"] for h in s.hits] == [h.chunk["chunk_id"] for h in duz]


def test_yazici_olusturulamazsa_duser(bm25, monkeypatch):
    import mevzuat_rag.rewrite as rwmod

    def boom(*a, **k):
        raise RuntimeError("anahtar yok")
    monkeypatch.setattr(rwmod, "QueryRewriter", boom)
    s = Arayici(retriever=bm25).ara("cayma hakkı")
    assert s.yeniden_yazim == BASARISIZ and "anahtar yok" in s.uyari and s.hits


def test_yeniden_yazim_kapali(bm25):
    s = Arayici(retriever=bm25, rewrite=False).ara("cayma hakkı")
    assert s.yeniden_yazim == KAPALI and s.uyari is None


def test_temel_kurulum_torch_gerektirmez():
    """Varsayılan hat sentence_transformers / torch import etmeden çalışmalı."""
    import subprocess
    import sys
    code = ("import sys; sys.path.insert(0,'src');"
            "from mevzuat_rag.pipeline import Arayici;"
            "a=Arayici(rewrite=False); a.ara('cayma hakkı');"
            "assert not {'torch','sentence_transformers','pymupdf'} & set(sys.modules), 'yüklendi'")
    r = subprocess.run([sys.executable, "-c", code], cwd=config.ROOT, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def test_varsayilan_yeniden_yazim_modeli_haiku():
    from mevzuat_rag.rewrite import REWRITE_MODEL, SERVER_FALLBACK_MODELS
    assert REWRITE_MODEL == "claude-haiku-5-5"
    assert REWRITE_MODEL not in SERVER_FALLBACK_MODELS  # Haiku 5.5'te sunucu tarafı fallback yok
