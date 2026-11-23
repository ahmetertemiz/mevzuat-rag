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


@pytest.mark.skipif(not (config.INDEX_DIR / "bge-m3" / "meta.json").exists(), reason="indeks yok")
def test_hibrit_arama_calisir():
    pytest.importorskip("sentence_transformers")
    r = Retriever()
    hits = r.search("cayma hakkı kaç gün", k=5, mode="hybrid")
    assert len(hits) == 5
    assert all(h.dense_rank and h.bm25_rank for h in hits)


@pytest.mark.skipif(not (config.INDEX_DIR / "bge-m3" / "meta.json").exists(), reason="indeks yok")
def test_indeks_hicbir_parcayi_kesmiyor():
    import json
    meta = json.loads((config.INDEX_DIR / "bge-m3" / "meta.json").read_text(encoding="utf-8"))
    assert meta["truncated"] == []
    assert meta["max_token_length"] <= meta["max_seq_length"]


def test_ek_sorgular_rrf_ile_birlestirilir(bm25):
    """Yeniden yazım: özgün sorgu ek sorgularla RRF'te birleşir; ek sorgu doğru maddeyi öne taşır."""
    alone = bm25.search("xyzqw", k=3, mode="bm25")
    with_extra = bm25.search("xyzqw", k=3, mode="bm25", extra_queries=["6502 m.48"])
    assert with_extra[0].chunk["madde_no"] == "48"
    assert alone == []  # eşleşmeyen özgün sorgu sıralamaya hiçbir şey eklemez


def test_eslesmeyen_bm25_sorgusu_rrfe_katki_vermez(bm25):
    assert bm25.search("xyzqw", k=5, mode="bm25") == []


def test_yeniden_yazim_promptu_kurallari():
    from mevzuat_rag import rewrite
    assert rewrite.MAX_QUERIES == 4
    assert "en fazla 4" in rewrite.SYSTEM_PROMPT
    assert "her konu ve her alt soru için en az bir sorgu" in rewrite.SYSTEM_PROMPT
    assert rewrite.cache_path().name.endswith(f"_p{rewrite.PROMPT_VERSION}.json")


# ------------------------------------------------------------------ deney seçenekleri (varsayılan dışı)

def test_varsayilan_birlestirme_degismedi(bm25):
    a = bm25.search("cayma hakkı", k=10, mode="bm25", extra_queries=["mesafeli sözleşme cayma"])
    b = bm25.search("cayma hakkı", k=10, mode="bm25", extra_queries=["mesafeli sözleşme cayma"], birlestirme="duz")
    assert [h.chunk["chunk_id"] for h in a] == [h.chunk["chunk_id"] for h in b]


def test_iki_asamali_rrf_ozgun_sorgunun_agirligini_korur(bm25):
    """Özgün sorgu 1. sırada bulsun; üç ek sorgu başka bir maddeyi öne çıkarsın.
    Düz RRF'te özgünün birincisi geriye düşer, iki aşamalıda ilk sıralarda kalır."""
    soru = "6502 m.80"                                    # TKHK-m80-1 özgün sorguda 1. sırada
    ek = ["veri sorumlusuna başvuru", "kurula şikâyet", "veri sorumlusuna başvuru süresi"]
    duz = [h.chunk["chunk_id"] for h in bm25.search(soru, k=50, mode="bm25", extra_queries=ek)]
    iki = [h.chunk["chunk_id"] for h in bm25.search(soru, k=50, mode="bm25", extra_queries=ek,
                                                     birlestirme="iki_asamali")]
    # iki aşamalıda özgünün birincisi ilk 2'de (1. sıra, ek sorguların birincisiyle eşit skorda)
    assert iki.index("TKHK-m80-1") <= 1
    # düz RRF'te üç ek sorgunun listeleri onu ilk 50'nin dışına iter
    assert "TKHK-m80-1" not in duz


def test_parca_cesitliligi(bm25):
    hits = bm25.search("6502 m.77 idari para cezası", k=8, mode="bm25", max_parca_madde=2)
    from collections import Counter
    say = Counter(f"{h.chunk['belge_kisa_ad']}:{h.chunk['madde_no']}" for h in hits)
    assert max(say.values()) <= 2
    tum = bm25.search("6502 m.77 idari para cezası", k=400, mode="bm25", max_parca_madde=2)
    assert len(tum) == len(bm25.search("6502 m.77 idari para cezası", k=400, mode="bm25"))  # hiçbir parça kaybolmaz


def test_prompt_v4_yalniz_genel_kural_ekler():
    from mevzuat_rag.rewrite import PROMPT_VERSION, SYSTEM_PROMPT, SYSTEM_PROMPT_V4, sistem_promptu
    assert PROMPT_VERSION == 3 and sistem_promptu() == SYSTEM_PROMPT
    eklenen = SYSTEM_PROMPT_V4.replace(SYSTEM_PROMPT.split("\nÖrnekler:\n")[0], "", 1)
    assert "kendi anahtar kelimelerini" in SYSTEM_PROMPT_V4
    assert "yan sözleşme" not in SYSTEM_PROMPT_V4 and "yan sözleşme" not in eklenen
