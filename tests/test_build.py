"""Gerçek PDF'ler üzerinde uçtan uca kontroller. Belgeler bir kez işlenir (oturum fixture'ı)."""
from collections import Counter

import pytest

from mevzuat_rag import config
from mevzuat_rag.build import build_document

REQUIRED = {"chunk_id", "belge_id", "belge_kisa_ad", "belge_adi", "tur", "durum", "madde_no",
            "madde_etiketi", "madde_basligi", "fikralar", "parca", "parca_sayisi", "dipnotlar",
            "degisiklik_notlari", "sayfalar", "indekse_dahil", "baglam_basligi", "metin", "arama_metni"}


@pytest.fixture(scope="session")
def results():
    return {d.kisa_ad: build_document(d) for d in config.DOCS}


@pytest.fixture(scope="session")
def chunks(results):
    return [c for r in results.values() for c in r.chunks]


@pytest.fixture(scope="session")
def by_id(chunks):
    return {c["chunk_id"]: c for c in chunks}


def _article(chunks, kisa, madde):
    return [c for c in chunks if c["belge_kisa_ad"] == kisa and c["madde_no"] == madde]


@pytest.mark.parametrize("kisa,n", [("TKHK", 95), ("ETK", 22), ("KVKK", 36), ("MSY", 25)])
def test_madde_sayilari(results, kisa, n):
    d = results[kisa].diag
    assert d["madde_sayisi"] == n
    assert d["bagimsiz_baslik_sayimi"] == n


def test_tum_dipnotlar_bir_maddeye_baglandi(results):
    for kisa, r in results.items():
        assert r.diag["baglanmayan_dipnotlar"] == [], kisa


def test_parca_semasi(chunks):
    ids = Counter(c["chunk_id"] for c in chunks)
    assert all(v == 1 for v in ids.values())
    for c in chunks:
        assert REQUIRED <= c.keys(), c["chunk_id"]
        assert c["metin"].strip(), c["chunk_id"]
        assert c["sayfalar"], c["chunk_id"]
        assert "⟨fn" not in c["metin"] and "⟨fn" not in c["arama_metni"], c["chunk_id"]
        # karar 8: bağlam başlığı arama metninin başında
        assert c["arama_metni"].startswith(c["baglam_basligi"] + "\n"), c["chunk_id"]


def test_parca_uzunluk_siniri(chunks):
    for c in chunks:
        if c["tur"] == "madde":
            assert len(c["metin"].split()) <= config.MAX_CHUNK_WORDS * 1.3, c["chunk_id"]


def test_sayfa_sonu_dipnotu_cumleyi_bolmuyor(chunks):
    """6563 m.11/3'te bir cümle sayfa sonunda bölünüyor ve arasına 3 numaralı dipnot giriyor."""
    text = " ".join(c["metin"] for c in _article(chunks, "ETK", "11"))
    assert "her türlü yardım ve kolaylığı göstermekle yükümlüdür" in text
    assert "teselsül" not in text  # dipnot metni gövdeye sızmamış


def test_aym_dipnotu_fikraya_bagli_ve_govdede_yok(chunks):
    c = _article(chunks, "ETK", "9")[0]
    aym = [d for d in c["dipnotlar"] if d["tur"] == "aym_karari"]
    assert len(aym) == 1 and aym[0]["konum"] == "fıkra 1" and "2/3/2027" in aym[0]["metin"]
    assert "Anayasa Mahkemesi" not in c["metin"]
    assert "değildir.2" not in c["metin"] and "sorumlu değildir." in c["metin"]


def test_baslik_dipnotlari_tum_parcalarda(chunks):
    parts = _article(chunks, "TKHK", "77")
    assert len(parts) > 1
    for c in parts:
        assert {d["no"] for d in c["dipnotlar"]} >= {"25", "26", "27"}
        assert c["madde_basligi"] == "Yaptırım hükümleri"


def test_mulga_madde_kaydi(chunks):
    [c] = _article(chunks, "ETK", "10")
    assert c["tur"] == "mulga" and c["durum"] == "mulga"
    assert c["mulga"]["tarih"] == "2022-07-01"
    assert "7416" in c["mulga"]["dayanak"]
    assert c["indekse_dahil"] is True  # karar 3: indeksten çıkarılmaz
    assert "yürürlükten kaldırılmıştır" in c["arama_metni"]


def test_harfli_ek_gecici_maddeler(chunks):
    nos = {(c["belge_kisa_ad"], c["madde_no"]) for c in chunks}
    for x in [("TKHK", "47/A"), ("TKHK", "77/A"), ("ETK", "Ek 4"), ("ETK", "Geçici 2"),
              ("KVKK", "Geçici 3"), ("MSY", "12/A")]:
        assert x in nos, x


def test_cayma_hakki_metni(chunks):
    [c] = _article(chunks, "MSY", "9")
    assert c["madde_basligi"] == "Cayma hakkı"
    assert "on dört gün içinde herhangi bir gerekçe göstermeksizin" in c["metin"]


def test_uzun_tanim_maddesi_giris_cumlesini_tasir(chunks):
    parts = _article(chunks, "TKHK", "3")
    assert len(parts) >= 2
    for c in parts:
        assert c["metin"].startswith("(1) Bu Kanunun uygulanmasında;")
    assert parts[-1]["metin"].rstrip().endswith("ifade eder.")


def test_ceza_tablolari_onayli_ve_bagli(results, chunks, by_id):
    tablolar = [c for c in chunks if c["tur"] == "tablo"]
    assert {c["belge_kisa_ad"] for c in tablolar} == {"TKHK", "ETK"}
    for c in tablolar:
        assert c["indekse_dahil"] is True  # kullanıcı onayı sonrası
        assert c["yil"] == 2026
        for row in c["satirlar"]:
            linked = by_id[row["ilgili_parca"]]
            if row["bolum"] == "guncel":
                assert row["fikra_no"] in linked["fikralar"], row
                assert linked["madde_no"] == c["ilgili_madde"]
            else:
                assert linked["madde_no"] == "Geçici 3"
        assert c["ilgili_parcalar"] == list(dict.fromkeys(r["ilgili_parca"] for r in c["satirlar"]))
    # bent bazında bölünmüş 6563 m.12/1: bent satırı, o bendi içeren parçaya bağlanır
    etk = next(c for c in tablolar if c["belge_kisa_ad"] == "ETK")
    h = next(r for r in etk["satirlar"] if r["bent"] == "(h) bendi")
    assert "h" in by_id[h["ilgili_parca"]]["bentler"]
    # 6502 tablosu notu hem metnin hem arama metninin başında
    tk = next(c for c in tablolar if c["belge_kisa_ad"] == "TKHK")
    note = "Bir satırda birden çok tutar varsa"
    assert tk["metin"].startswith(note)
    assert tk["arama_metni"].split("\n", 1)[1].startswith(note)
    for kisa in ("TKHK", "ETK"):
        t = results[kisa].table
        assert Counter(t.hucre_sayilari) == Counter(t.ham_sayilar)


def test_ceza_tablosu_bilinen_degerler(results):
    etk = {(r.fikra, r.bent): r.tutar for r in results["ETK"].table.satirlar}
    assert etk[("Birinci fıkrasındaki ceza tutarları", "(h) bendi")] == "1.431.033"
    assert etk[("Birinci fıkrasının (a) bendindeki cezanın alt ve üst sınırları", None)] == "2.859-14.309"
    tk = [r.tutar for r in results["TKHK"].table.satirlar
          if r.fikra == "Dördüncü fıkrasındaki ceza miktarı" and r.bolum == "guncel"]
    assert tk == ["31.902.048", "22.329"]
    # sayfa geçişinde etiketsiz devam satırı bir önceki fıkraya bağlanır
    on_dort = [r.tutar for r in results["TKHK"].table.satirlar
               if r.fikra == "On dördüncü fıkrasındaki ceza miktarları"]
    assert on_dort == ["6.380.408", "1.987.014", "99.315"]


def test_belge_ustverisi(results):
    for r in results.values():
        m = r.meta
        assert m["indirme_tarihi"] == "2026-11-23"
        assert m["son_degisiklik"]["metin_ici_en_son_degisiklik_notu"]["tarih"]
        assert m["son_degisiklik"]["pdf_olusturma_tarihi"]
        assert m["resmi_gazete"]["tarih"] and m["resmi_gazete"]["sayi"]
    assert results["TKHK"].meta["tam_ad"] == "6502 sayılı Tüketicinin Korunması Hakkında Kanun"
    assert results["MSY"].meta["resmi_gazete"] == {"tarih": "2014-11-27", "sayi": "29188"}
