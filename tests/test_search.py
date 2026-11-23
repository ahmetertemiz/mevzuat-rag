"""Tokenizer, BM25 madde-numarası araması ve RRF testleri. Model gerektirmez
(model gerektiren test, indeks yoksa atlanır)."""
import pytest

from mevzuat_rag import config
from mevzuat_rag.retrieve import Retriever, rrf
from mevzuat_rag.textnorm import document_tokens, query_tokens, word_tokens


@pytest.mark.parametrize("q,ref", [
    ("6502 m.48", "md:48"),
    ("6502 m. 48", "md:48"),
    ("madde 48", "md:48"),
    ("md. 48", "md:48"),
    ("48. madde", "md:48"),
    ("48 inci maddesi", "md:48"),
    ("47/A", "md:47/a"),
    ("madde 47/A", "md:47/a"),
    ("MSY m.12/A", "md:12/a"),
    ("Ek 1", "md:ek1"),
    ("ek madde 1", "md:ek1"),
    ("Geçici 2", "md:gecici2"),
    ("GEÇİCİ MADDE 2", "md:gecici2"),
])
def test_madde_numarasi_belirteci(q, ref):
    assert ref in query_tokens(q)


def test_tarih_madde_sanilmaz():
    toks = query_tokens("1/7/2022 tarihli değişiklik")
    assert not any(t.startswith("md:") for t in toks)


def test_kanun_numarasi_korunur_ve_birlesik_belirtec_uretilir():
    assert query_tokens("6502 m.48") == ["md:48", "md:tkhk:48", "6502"]
    assert "md:kvkk:gecici2" in query_tokens("KVKK geçici madde 2")
    assert "md:msy:12/a" in query_tokens("Mesafeli Sözleşmeler Yönetmeliği madde 12/A")
    assert "md:tkhk:47/a" in document_tokens(
        "6502 sayılı Tüketicinin Korunması Hakkında Kanun (TKHK) · Madde 47/A · Doğrudan satış", "")


def test_govdedeki_atif_belirtece_cevrilmez():
    toks = document_tokens("TKHK · Madde 77 · Yaptırım hükümleri", "48 inci maddesinin ikinci fıkrası")
    assert "md:77" in toks and "md:48" not in toks


def test_turkce_kucuk_harf_ve_f5():
    assert word_tokens("CAYMA HAKKINI İADE") == ["cayma", "hakkı", "iade"]
    assert word_tokens("hakkı hakkının") == ["hakkı", "hakkı"]
    assert "ve" not in word_tokens("ayıplı ve bozuk")


def test_rrf():
    s = rrf([[0, 1, 2], [2, 1, 0]], 3, k=60)
    assert s[1] == pytest.approx(2 / 62)
    assert s[0] == pytest.approx(1 / 61 + 1 / 63) == s[2]


@pytest.fixture(scope="module")
def bm25():
    return Retriever(load_model=False)


@pytest.mark.parametrize("q,belge,madde", [
    ("6502 m.48", "TKHK", "48"),
    ("madde 48", "TKHK", "48"),
    ("TKHK 47/A", "TKHK", "47/A"),
    ("6502 sayılı kanun 77/A maddesi", "TKHK", "77/A"),
    ("6563 ek madde 1", "ETK", "Ek 1"),
    ("Ek 4", "ETK", "Ek 4"),
    ("KVKK geçici madde 2", "KVKK", "Geçici 2"),
    ("6502 Geçici 3", "TKHK", "Geçici 3"),
    ("Mesafeli Sözleşmeler Yönetmeliği madde 12/A", "MSY", "12/A"),
    ("6698 m.11", "KVKK", "11"),
])
def test_bm25_madde_numarasiyla_bulur(bm25, q, belge, madde):
    top = bm25.search(q, k=1, mode="bm25")[0].chunk
    assert (top["belge_kisa_ad"], top["madde_no"]) == (belge, madde)


def test_indeks_disi_parca_aranmaz(bm25):
    assert all(c["indekse_dahil"] for c in bm25.chunks)


@pytest.mark.skipif(not (config.INDEX_DIR / "meta.json").exists(), reason="indeks yok")
def test_hibrit_arama_calisir():
    r = Retriever()
    hits = r.search("cayma hakkı kaç gün", k=5, mode="hybrid")
    assert len(hits) == 5
    assert all(h.dense_rank and h.bm25_rank for h in hits)


@pytest.mark.skipif(not (config.INDEX_DIR / "meta.json").exists(), reason="indeks yok")
def test_indeks_hicbir_parcayi_kesmiyor():
    import json
    meta = json.loads((config.INDEX_DIR / "meta.json").read_text(encoding="utf-8"))
    assert meta["truncated"] == []
    assert meta["max_token_length"] <= meta["max_seq_length"]
