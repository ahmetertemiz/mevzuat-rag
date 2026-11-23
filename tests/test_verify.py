"""Alıntı doğrulama ve sayı tutarlılığı (model çağrısı yok)."""
import json

import pytest

from mevzuat_rag import config
from mevzuat_rag.verify import alinti_dogrula, norm_alinti, sayi_tutarliligi, sayilar, tr_sayi


@pytest.fixture(scope="module")
def parcalar():
    with config.CHUNKS_PATH.open(encoding="utf-8") as f:
        return {c["chunk_id"]: c for c in map(json.loads, f)}


# ------------------------------------------------------------------ alıntı

def test_kelimesi_kelimesine_alinti_dogrulanir(parcalar):
    p = parcalar["MSY-m9-1"]
    ok, _ = alinti_dogrula("on dört gün içinde herhangi bir gerekçe göstermeksizin", p)
    assert ok


@pytest.mark.parametrize("alinti", [
    "On dört gün içinde herhangi bir gerekçe göstermeksizin.",         # büyük harf + nokta
    "“on dört gün içinde  herhangi bir gerekçe göstermeksizin”",       # tırnak + çift boşluk
    "on dört gün içinde\nherhangi bir gerekçe göstermeksizin",          # satır sonu
])
def test_bosluk_tirnak_buyukharf_farklari_tolere_edilir(parcalar, alinti):
    assert alinti_dogrula(alinti, parcalar["MSY-m9-1"])[0]


def test_tire_farklari_tolere_edilir():
    p = {"metin": "mühendislik fakültelerinin elektronik, elektrik-elektronik bölümlerinden", "dipnotlar": []}
    assert alinti_dogrula("elektrik–elektronik bölümlerinden mezun", p)[0] is False  # "mezun" yok
    assert alinti_dogrula("fakültelerinin elektronik, elektrik—elektronik bölümlerinden", p)[0]
    assert alinti_dogrula("elektrik elektronik bölümlerinden", p)[0]


def test_degisiklik_notu_atlanarak_alinti_kabul(parcalar):
    p = parcalar["MSY-m13-1"]  # "on (Ek ibare:RG-23/8/2022-31932)dört gün içinde"
    assert alinti_dogrula("on dört gün içinde malı satıcı veya sağlayıcıya", p)[0]


def test_dipnottan_alinti_kabul(parcalar):
    p = parcalar["ETK-m9-1"]
    assert alinti_dogrula("tüketici sözleşmeleri” yönünden iptal edilmiştir", p)[0]


def test_baska_parcadaki_alinti_reddedilir(parcalar):
    # metin MSY-m9-1'de var ama gösterilen parça TKHK-m11-1
    ok, neden = alinti_dogrula("on dört gün içinde herhangi bir gerekçe göstermeksizin", parcalar["TKHK-m11-1"])
    assert not ok and "geçmiyor" in neden


def test_uydurma_ve_kisa_alinti_reddedilir(parcalar):
    p = parcalar["MSY-m9-1"]
    assert not alinti_dogrula("on gün içinde herhangi bir gerekçe göstermeksizin", p)[0]
    assert not alinti_dogrula("tüketici", p)[0]
    assert not alinti_dogrula("on dört gün", None)[0]


def test_norm_alinti():
    # Türkçe küçük harf (İ->i, I->ı), tırnak birleştirme, baş/son noktalama ve boşluk atılır
    assert norm_alinti("  “İADE” Işık… ") == 'iade" ışık'
    assert norm_alinti("Satıcı—sağlayıcı") == "satıcı sağlayıcı"


# ------------------------------------------------------------------ sayılar

@pytest.mark.parametrize("yazi,deger", [
    ("on dört", 14), ("otuz", 30), ("yüz bin", 100_000), ("iki yüz elli bin", 250_000),
    ("bin", 1_000), ("beş milyon", 5_000_000), ("yedi", 7),
])
def test_tr_sayi(yazi, deger):
    assert tr_sayi(yazi) == deger


def test_rakam_ve_yazi_ayni_degere_esler():
    assert sayilar("on dört gün") == sayilar("14 gün") == {14}
    assert sayilar("yüz bin Türk Lirası") == {100_000}
    assert sayilar("1.987.014 TL") == {1_987_014}
    assert sayilar("yüzde on") == {10}
    assert sayilar("bir ürün aldım") == set()       # belirsiz "bir" sayı değil
    assert sayilar("bir ayıplı mal") == set()


def test_sayi_tutarliligi_rakam_yazi_eslesmesi(parcalar):
    p = parcalar["MSY-m9-1"]
    assert sayi_tutarliligi("Cayma süresi 14 gündür.", [], [p]) == []          # parçada "on dört gün"
    assert sayi_tutarliligi("Cayma süresi on dört gündür.", [], [p]) == []


def test_sayi_tutarliligi_uydurma_sayiyi_yakalar(parcalar):
    p = parcalar["MSY-m9-1"]
    assert sayi_tutarliligi("Cayma süresi on gündür.", [], [p]) == [10]
    assert sayi_tutarliligi("Cayma süresi 30 gündür.", [], [p]) == [30]


def test_sayi_tutarliligi_madde_ve_fikra_numarasi(parcalar):
    p = parcalar["TKHK-m48-1"]
    # madde 48 ve fıkra 4 parça kimliğinde; 6502 kanun numarası belge kaydında
    belgeler = {p["belge_id"]: {"numara": "6502", "tam_ad": "6502 sayılı Tüketicinin Korunması Hakkında Kanun"}}
    assert sayi_tutarliligi("6502 sayılı Kanunun 48. maddesinin 4. fıkrasına göre", [], [p], belgeler) == []
    assert sayi_tutarliligi("6502 sayılı Kanunun 49. maddesine göre", [], [p], belgeler) == [49]


def test_sayi_tutarliligi_tutar(parcalar):
    t = parcalar["TKHK-tablo2026-1"]
    assert sayi_tutarliligi("2026 yılında tutar 1.987.014 TL'dir.", [], [t]) == []
    assert sayi_tutarliligi("2026 yılında tutar 1.987.015 TL'dir.", [], [t]) == [1_987_015]


def test_sayi_tutarliligi_alintidaki_sayi_yeter():
    p = {"metin": "x", "dipnotlar": []}
    assert sayi_tutarliligi("Süre otuz gündür.", ["en geç otuz gün içinde"], [p]) == []


@pytest.mark.parametrize("metin,deger", [
    ("on gündür", {10}), ("on dört günlüktür", {14}), ("altı aydır", {6}), ("üç ay içinde", {3}),
    ("beş yıllık", {5}), ("otuz bin liradır", {30_000}), ("on katı", {10}),
    ("bir ayıp", set()), ("iki ayıplı mal", set()),
])
def test_ekli_birimler(metin, deger):
    assert sayilar(metin) == deger


# ------------------------------------------------------------------ birimli sayı tutarlılığı

def test_birim_farki_yakalanir():
    p = {"metin": "(1) ... (2) Bu süre her halükarda bir yıl sonra sona erer.", "dipnotlar": [], "fikralar": [1, 2]}
    # kaynakta "2" yalnız fıkra numarası; "iki yıl" süresi kaynakta yok
    assert sayi_tutarliligi("Süre iki yıl sonra sona erer.", [], [p]) == [2]
    assert sayi_tutarliligi("Süre bir yıl sonra sona erer.", [], [p]) == []


def test_gun_ve_is_gunu_ayrilir():
    p = {"metin": "talebin yöneltilmesinden itibaren otuz iş gününü geçemez", "dipnotlar": []}
    assert sayi_tutarliligi("En fazla otuz iş günüdür.", [], [p]) == []
    assert sayi_tutarliligi("En fazla 30 iş günüdür.", [], [p]) == []
    assert sayi_tutarliligi("En fazla otuz gündür.", [], [p]) == [30]


def test_tutar_birimiyle(parcalar):
    t = parcalar["ETK-tablo2026-1"]
    assert sayi_tutarliligi("Ceza 2.859 TL ile 28.620 TL arasındadır.", [], [t]) == []
    assert sayi_tutarliligi("Ceza 2.859 gündür.", [], [t]) == [2859]


def test_birimsiz_sayilar_deger_olarak_denetlenir(parcalar):
    p = parcalar["ETK-m9-1"]   # dipnotta 12/2/2026 ve 2/3/2027
    assert sayi_tutarliligi("Karar 2/3/2027 tarihinde yürürlüğe girer.", [], [p]) == []
    assert sayi_tutarliligi("Karar 2/3/2028 tarihinde yürürlüğe girer.", [], [p]) == [2028]
