"""Bağlam kurma (model çağrısı yok)."""
import pytest

from mevzuat_rag.context import MAX_TABLO_EK, kur
from mevzuat_rag.retrieve import Retriever


@pytest.fixture(scope="module")
def r():
    return Retriever(load_model=False)


def _by_id(r, *ids):
    m = {c["chunk_id"]: c for c in r.chunks}
    return [m[i] for i in ids]


def test_k_siniri_ve_sira(r):
    hits = r.search("cayma hakkı", k=20, mode="bm25")
    b = kur(hits, "cayma hakkı", r, k=8)
    assert [p["chunk_id"] for p in b.parcalar[:8]] == [h.chunk["chunk_id"] for h in hits[:8]]


def test_dipnotlar_tekillestirilir(r):
    parcalar = _by_id(r, "TKHK-m77-1", "TKHK-m77-2", "TKHK-m77-3")  # 25-27 başlık dipnotları her parçada
    b = kur(parcalar, "ceza", r)
    assert {"TKHK-dn25", "TKHK-dn26", "TKHK-dn27"} <= set(b.dipnotlar)
    assert b.metin.count("[TKHK-dn26]") == 1


def test_mulga_kaydi_isaretlenir(r):
    b = kur(_by_id(r, "ETK-m10-1"), "kişisel veriler", r)
    assert "MÜLGA" in b.metin and "2022-07-01" in b.metin


def test_aym_dipnotu_baglamda(r):
    b = kur(_by_id(r, "ETK-m9-1"), "pazaryeri sorumluluğu", r)
    assert any(d["tur"] == "aym_karari" for d in b.dipnotlar.values())
    assert "2/3/2027" in b.metin


def test_tablo_bagli_madde_parcalariyla_gelir(r):
    b = kur(_by_id(r, "TKHK-tablo2026-1"), "kapıdan satış yetki idari para cezası", r)
    assert 1 <= len(b.ek_parcalar) <= MAX_TABLO_EK
    assert all(cid.startswith("TKHK-m77-") for cid in b.ek_parcalar)
    assert "ceza tablosunun bağlı olduğu madde parçası" in b.metin
    assert len({p["chunk_id"] for p in b.parcalar}) == len(b.parcalar)  # tekrar yok


def test_tablo_ekleri_zaten_bagliysa_eklenmez(r):
    parcalar = _by_id(r, "ETK-tablo2026-1", "ETK-m12-1", "ETK-m12-2", "ETK-m12-3", "ETK-m12-4", "ETK-m12-5")
    b = kur(parcalar, "ceza", r)
    assert b.ek_parcalar == []


def test_belge_surum_bilgisi(r):
    b = kur(_by_id(r, "MSY-m9-1"), "cayma", r)
    assert "<belgeler>" in b.metin and "indirildi: 2026-11-23" in b.metin
    assert "PDF metin tarihi" in b.metin


def test_yeniden_yazilmis_sorgu_baglama_girmez(r):
    # bağlam yalnız soru ve parçalardan kurulur; kur() sorgu listesi almaz
    import inspect
    assert "sorgular" not in inspect.signature(kur).parameters


def test_tablo_atfi_olan_dipnot_tabloyu_baglama_ekler(r):
    """A03 hatası: m.77/2 parçası bağlamda, tablo değil -> tablo otomatik eklenir."""
    b = kur(_by_id(r, "TKHK-m5-1", "TKHK-m77-1"), "haksız şart cezası", r)
    assert "TKHK-tablo2026-1" in b.ek_parcalar
    assert "Tutarlar her yıl güncellenir; güncel tutar bu tablodadır" in b.metin


def test_tablo_atfi_yoksa_tablo_eklenmez(r):
    b = kur(_by_id(r, "MSY-m9-1", "TKHK-m48-1"), "cayma", r)
    assert not any(c.startswith(("TKHK-tablo", "ETK-tablo")) for c in b.ek_parcalar)


def test_etk_m12_dipnotu_etk_tablosunu_ekler(r):
    b = kur(_by_id(r, "ETK-m12-1"), "ceza", r)
    assert "ETK-tablo2026-1" in b.ek_parcalar and "TKHK-tablo2026-1" not in b.ek_parcalar
