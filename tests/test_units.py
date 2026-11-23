"""Küçük, PDF'e bağlı olmayan birim testleri."""
import pytest

from mevzuat_rag import chunk as ch
from mevzuat_rag.build import _mulga_info, _slug
from mevzuat_rag.extract import ARTICLE_HEADER_RE, Paragraph, _join
from mevzuat_rag.textnorm import tr_lower, tr_title


@pytest.mark.parametrize("line,tip,no", [
    ("MADDE 1 – (1) Bu Kanunun amacı", None, "1"),       # en-dash
    ("MADDE 9- (Başlığı ile Birlikte Değişik:1/7/2022-7416/3 md.)", None, "9"),  # tire
    ("MADDE 20 − (1) Satıcı veya sağlayıcı", None, "20"),  # eksi işareti
    ("MADDE 47/A- (Ek:24/10/2024-7529/6 md.)", None, "47/A"),
    ("EK MADDE 1- (Ek:1/7/2022-7416/7 md.)", "EK", "1"),
    ("GEÇİCİ MADDE 2 – (1) Bu maddeyi", "GEÇİCİ", "2"),
])
def test_madde_basligi_kaliplari(line, tip, no):
    m = ARTICLE_HEADER_RE.match(line)
    assert m
    assert (m.group("tip") or "").strip() == (tip or "")
    assert m.group("no") == no


def test_madde_basligi_atif_cumlesini_yakalamaz():
    assert not ARTICLE_HEADER_RE.match("48 inci maddesinin ikinci fıkrası")
    assert not ARTICLE_HEADER_RE.match("Ek Madde 1, Ek Madde 2,")


def test_dipnot_isareti_ayristirma():
    known = {str(i) for i in range(1, 33)}
    assert ch.segment_markers("252627", known) == ["25", "26", "27"]
    assert ch.segment_markers("2324", known) == ["23", "24"]
    assert ch.segment_markers("12", known) == ["12"]
    assert ch.segment_markers("45", {"1", "2", "3", "4", "5"}) == ["4", "5"]


def test_degisiklik_notlari():
    t = ("(1) (Değişik:1/7/2022-7416/5 md.) Bakanlık yetkilidir. (Ek cümle:1/7/2022-7416/5 md.) "
         "Satıcı (Ek ibare:RG-23/8/2022-31932) ile (Değişik: 2/1/2017-KHK-684/8 md.; Aynen kabul: "
         "1/2/2018-7079/1 md.) birlikte (a) bendinde")
    notes = ch.find_amendments(t)
    assert len(notes) == 4
    clean = ch.strip_amendments(t)
    assert "Değişik" not in clean and "Ek ibare" not in clean
    assert "(a) bendinde" in clean and clean.startswith("(1) Bakanlık")


def test_mulga_bilgisi():
    k = _mulga_info("(Mülga:1/7/2022-7416/4 md.)", "kanun")
    assert k["tarih"] == "2022-07-01"
    assert k["dayanak"] == "7416 sayılı Kanunun 4. maddesi"
    y = _mulga_info("(Mülga:RG-23/8/2022-31932)", "yonetmelik")
    assert y["tarih"] == "2022-08-23" and "31932" in y["dayanak"]


def test_turkce_kucuk_harf_ve_baslik():
    assert tr_lower("İADE IŞIK") == "iade ışık"
    assert tr_title("TÜKETİCİNİN KORUNMASI HAKKINDA KANUN") == "Tüketicinin Korunması Hakkında Kanun"
    assert tr_title("KANUNUN 77 NCİ MADDESİ") == "Kanunun 77 nci Maddesi"


def test_satir_birlestirme_tireyi_korur():
    assert _join("elektrik-", "elektronik") == "elektrik-elektronik"
    assert _join("(Ek:1/7/2022-", "7416/2 md.)") == "(Ek:1/7/2022-7416/2 md.)"
    assert _join("bir", "satır") == "bir satır"


def test_slug():
    assert _slug("48") == "m48"
    assert _slug("47/A") == "m47a"
    assert _slug("Ek 1") == "ek1"
    assert _slug("Geçici 2") == "gecici2"


def _paras(*texts):
    return [Paragraph(t, 1, 100.0) for t in texts]


def test_baslik_onceki_paragraftan_alinir_ve_fikralar_ayrilir():
    arts = ch.parse_articles(_paras(
        "BİRİNCİ BÖLÜM", "Genel Hükümler",
        "Amaç", "MADDE 1 – (1) Birinci fıkra.", "(2) İkinci fıkra.",
        "Cezai hükümler⟨fn:45⟩", "MADDE 2- (Değişik:1/7/2022-7416/6 md.)", "(1) Ceza fıkrası.",
    ))
    assert [a.madde_no for a in arts] == ["1", "2"]
    assert arts[0].baslik == "Amaç" and arts[0].bolum == "Birinci Bölüm: Genel Hükümler"
    assert [f.no for f in arts[0].fikralar] == [1, 2]
    assert arts[1].baslik == "Cezai hükümler" and arts[1].baslik_fn == ["45"]
    assert arts[1].intro.startswith("(Değişik:")
    assert [f.no for f in arts[1].fikralar] == [1]


def test_uzun_fikra_bent_sinirindan_bolunur():
    bents = [f"{c}) " + " ".join(["kelime"] * 40) + "," for c in "abcdefgh"]
    arts = ch.parse_articles(_paras("Tanımlar", "MADDE 3 – (1) Bu Kanunun uygulanmasında;", *bents, "ifade eder."))
    pieces = ch.split_article(arts[0], max_words=100)
    assert len(pieces) > 1
    # her parça giriş cümlesiyle başlar, kapanış son parçada
    assert all(p.text_parts[0].startswith("(1) Bu Kanunun uygulanmasında;") for p in pieces)
    assert pieces[-1].text_parts[-1] == "ifade eder."
    # bentler kaybolmadan ve sırası bozulmadan dağıtıldı
    assert [b for p in pieces for b in p.bentler] == list("abcdefgh")
