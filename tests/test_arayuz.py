"""Arayüz mantığı (src/mevzuat_rag/arayuz.py) ve Streamlit sayfası (streamlit_app.py)."""
import datetime as dt
import os
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from mevzuat_rag.arayuz import (GunlukSayac, SayacliIstemci, SinirAsildi, fikra_bul, kisa_atif,
                                madde_tam_metni, yeniden_yazici_kur)
from mevzuat_rag.context import belge_kaydi
from mevzuat_rag.retrieve import load_chunks

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def C():
    return {c["chunk_id"]: c for c in load_chunks()}


@pytest.fixture(scope="module")
def B():
    return belge_kaydi()


@pytest.mark.parametrize("cid,alinti,beklenen", [
    ("TKHK-m24-1", "on dört gün içinde herhangi bir gerekçe göstermeksizin", "6502 m.24/1"),
    ("TKHK-m77-2", "47 nci maddesinin ikinci fıkrasında belirtilen yükümlülüklere", "6502 m.77/5"),
    ("MSY-m9-1", "on dört gün içinde herhangi bir gerekçe göstermeksizin", "MSY m.9/1"),
    ("MSY-m12a-1", "ön bilgilendirmenin yapılması", "MSY m.12/A, f.3"),
    ("ETK-m9-1", "Anayasa Mahkemesinin", "6563 m.9, dipnot"),
    ("ETK-ek1-1", None, "6563 ek m.1"),
    ("TKHK-gecici3-1", None, "6502 geç. m.3"),
    ("TKHK-tablo2026-1", None, "6502 ceza tablosu (2026)"),
])
def test_kisa_atif(C, B, cid, alinti, beklenen):
    assert kisa_atif(C[cid], B, alinti) == beklenen


def test_fikra_bulunamazsa_yalniz_madde(C, B):
    assert fikra_bul(C["TKHK-m24-1"], "bu cümle hiçbir yerde geçmiyor") is None
    assert kisa_atif(C["TKHK-m24-1"], B, "bu cümle hiçbir yerde geçmiyor") == "6502 m.24"


def test_madde_tam_metni_bolunmus_maddeyi_birlestirir(C):
    tum = list(C.values())
    t = madde_tam_metni(C["TKHK-m77-3"], tum)
    assert t.index("(1)") < t.index("(5)") < t.index("(9)")
    assert madde_tam_metni(C["TKHK-tablo2026-1"], tum) == C["TKHK-tablo2026-1"]["metin"]


# ------------------------------------------------------------------ günlük sınır

def test_gunluk_sayac_sinir_ve_gun_degisimi():
    gun = [dt.date(2026, 11, 23)]
    s = GunlukSayac(2, saat=lambda: gun[0])
    s.al(); s.al()
    assert s.kalan() == 0
    with pytest.raises(SinirAsildi):
        s.al()
    gun[0] = dt.date(2026, 11, 24)
    assert s.kalan() == 2 and s.kullanilan() == 0


class _Ham:
    def __init__(self):
        self.calls = []
        self.messages = SimpleNamespace(create=lambda **kw: self.calls.append(("m", kw)) or "ok")
        self.beta = SimpleNamespace(messages=SimpleNamespace(
            create=lambda **kw: self.calls.append(("b", kw)) or "ok"))


def test_sayacli_istemci_her_cagriyi_sayar_ve_durdurur():
    s = GunlukSayac(2)
    ham = _Ham()
    ist = SayacliIstemci(ham, s)
    ist.messages.create(model="x")
    ist.beta.messages.create(model="y")
    assert s.kalan() == 0 and ist.cagri_sayisi == 2
    with pytest.raises(SinirAsildi):
        ist.messages.create(model="z")
    assert len(ham.calls) == 2   # sınır aşılınca API'ye gidilmez


def test_kendi_anahtari_sayilmaz():
    ist = SayacliIstemci(_Ham(), None)
    for _ in range(5):
        ist.messages.create(model="x")
    assert ist.cagri_sayisi == 5


def test_yeniden_yazici_kur_yapiciyla_ayni_oznitelikler():
    """rewrite.py değişirse (yeni öznitelik) bu test uyarır."""
    import inspect

    from mevzuat_rag.rewrite import QueryRewriter
    kaynak = inspect.getsource(QueryRewriter.__init__)
    yapici = set(__import__("re").findall(r"self\.(\w+)\s*=", kaynak))
    rw = yeniden_yazici_kur(_Ham())
    assert yapici <= set(vars(rw)), yapici - set(vars(rw))


def test_yeniden_yazici_verilen_istemciyi_kullanir():
    class Ist(_Ham):
        def __init__(self):
            super().__init__()
            self.messages = SimpleNamespace(create=self._c)

        def _c(self, **kw):
            self.calls.append(kw)
            return SimpleNamespace(stop_reason="end_turn",
                                   content=[SimpleNamespace(type="text", text=json.dumps({"sorgular": ["cayma hakkı süresi"]}))],
                                   usage=SimpleNamespace(input_tokens=10, output_tokens=5))
    ist = Ist()
    r = yeniden_yazici_kur(ist).rewrite("Cayma süresi nedir?")
    assert r.sorgular == ["cayma hakkı süresi"] and len(ist.calls) == 1


# ------------------------------------------------------------------ yayın ortamı

def test_requirements_yayin_ortaminda_torch_ve_pymupdf_yok():
    req = (ROOT / "requirements.txt").read_text(encoding="utf-8").lower()
    satirlar = [s.split("==")[0].strip() for s in req.splitlines() if s.strip() and not s.startswith("#")]
    assert "streamlit" in satirlar
    for yasak in ("torch", "pymupdf", "sentence-transformers", "fitz"):
        assert yasak not in satirlar


def test_gizli_dosyalar_gitignore_icinde():
    gi = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert ".env" in gi and ".streamlit/secrets.toml" in gi


# ------------------------------------------------------------------ Streamlit sayfası (AppTest, sahte API)

GIZLI = "sk-ant-test-GIZLI-ANAHTAR-123"


class _SahteAnthropic:
    """anthropic.Anthropic yerine: yeniden yazımda sorgu, cevapta MSY m.9'a dayanan bir cümle döner."""
    olusturulan: list = []

    def __init__(self, api_key=None, **kw):
        type(self).olusturulan.append(api_key)
        self.messages = SimpleNamespace(create=self._create)
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._create))

    def _create(self, **kw):
        if "sorgular" in json.dumps(kw.get("output_config", {})):
            out = {"sorgular": ["mesafeli sözleşme cayma hakkı süresi"]}
        else:
            out = {"durum": "cevaplandi", "bulunamayan": [], "uyarilar": [], "cumleler": [{
                "metin": "Tüketici on dört gün içinde gerekçe göstermeden cayabilir.",
                "dayanaklar": [{"parca_id": "MSY-m9-1",
                                "alinti": "on dört gün içinde herhangi bir gerekçe göstermeksizin"}]}]}
        return SimpleNamespace(stop_reason="end_turn", content=[SimpleNamespace(type="text", text=json.dumps(out))],
                               usage=SimpleNamespace(input_tokens=100, output_tokens=50))


@pytest.fixture
def app(monkeypatch):
    import anthropic
    import streamlit as st
    from streamlit.testing.v1 import AppTest

    monkeypatch.setattr(anthropic, "Anthropic", _SahteAnthropic)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")          # .env okunmasın (setdefault)
    monkeypatch.delenv("GUNLUK_CAGRI_SINIRI", raising=False)
    _SahteAnthropic.olusturulan = []
    st.cache_resource.clear()

    def yap(**env):
        for k, v in env.items():
            monkeypatch.setenv(k, v)
        st.cache_resource.clear()
        return AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=30)
    yield yap
    st.cache_resource.clear()


def _metinler(at) -> str:
    parcalar = []
    for tur in ("markdown", "caption", "error", "warning", "info", "text", "title", "subheader"):
        parcalar += [str(getattr(e, "value", "")) for e in getattr(at, tur)]
    parcalar += [str(getattr(e, "label", "")) for e in at.button]
    return "\n".join(parcalar)


def test_anahtar_yoksa_sor_devre_disi(app):
    at = app().run()
    assert not at.exception
    assert at.button[0].disabled
    assert "Bu demo kendi Anthropic API anahtarınızla çalışır" in _metinler(at)


def test_ornek_soru_cevap_ve_kaynak_gosterir(app):
    at = app(ANTHROPIC_API_KEY="sahte-ortak").run()
    at.button(key="ornek_0").click().run()            # örnek soru metni kutuya yazılır ve çalışır
    assert not at.exception and at.text_area(key="soru").value.startswith("Abonelik")
    at.text_area(key="soru").input("Mesafeli sözleşmelerde cayma hakkı süresi kaç gündür?")
    at.button[0].click().run()
    assert not at.exception
    m = _metinler(at)
    assert "on dört gün içinde gerekçe göstermeden cayabilir" in m
    assert "Hukuki tavsiye değildir" in m and "2026-11-23" in m
    assert "Bugün kalan ortak çağrı: **296 / 300**" in m   # iki soru × (yeniden yazım + cevap)
    assert "Kayıt sırasında" not in m                      # canlı cevapta işaret yok
    assert "MSY m.9/1" in str([b.proto for b in at.get("popover")])


def test_gunluk_sinir_dolunca_cagri_yapilmaz(app):
    at = app(ANTHROPIC_API_KEY="sahte-ortak", GUNLUK_CAGRI_SINIRI="1").run()
    at.button(key="ornek_1").click().run()
    assert not at.exception
    assert any("Günlük sınır doldu" in str(e.proto.title) or "sınırı doldu" in e.value for e in at.error)
    assert "on dört gün" not in _metinler(at)


def test_ziyaretci_anahtari_kullanilir_ve_gorunmez(app):
    at = app().run()
    at.text_input(key="ziyaretci_anahtari").input(GIZLI).run()
    at.button(key="ornek_2").click().run()
    assert not at.exception
    assert GIZLI in _SahteAnthropic.olusturulan              # istemciye verildi
    assert GIZLI not in _metinler(at)                         # ekranda yok
    assert GIZLI not in os.environ.get("ANTHROPIC_API_KEY", "")
    assert "Sizin anahtarınız kullanılıyor" in _metinler(at)


# ------------------------------------------------------------------ kayıtlı örnek cevaplar

def test_ornek_cevaplar_dosyasi_ornek_sorularla_eslesir():
    import ast

    from mevzuat_rag.arayuz import cevap_yukle, ornek_cevaplari_oku
    agac = ast.parse((ROOT / "streamlit_app.py").read_text(encoding="utf-8"))
    sorular = next(ast.literal_eval(n.value) for n in agac.body
                   if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "ORNEK_SORULAR")
    k = ornek_cevaplari_oku()
    assert set(k["cevaplar"]) == set(sorular)
    assert k["uretim_tarihi"] and k["model"]
    for v in k["cevaplar"].values():
        c = cevap_yukle(v["cevap"])
        assert c.cumleler and all(cm.dogrulandi for cm in c.cumleler)
        assert c.arama.get("sorgular") and c.baglam_parcalari and c.kaynaklar


def test_anahtarsiz_ornek_soru_kayitli_cevabi_gosterir(app):
    from mevzuat_rag.arayuz import ornek_cevaplari_oku
    at = app().run()
    at.button(key="ornek_1").click().run()
    assert not at.exception
    m = _metinler(at)
    assert "Kayıtlı örnek cevap (üretim tarihi" in m
    ilk = ornek_cevaplari_oku()["cevaplar"][at.text_area(key="soru").value]["cevap"]["cumleler"][0]["metin"]
    assert ilk in m                                        # kayıtlı cümle aynı çizim koduyla gösterildi
    assert "6502 m.56" in str([b.proto for b in at.get("popover")])
    assert _SahteAnthropic.olusturulan == []               # hiçbir API istemcisi kurulmadı
    assert "Kayıt sırasında (" in m and "Bu gösterimde model çağrısı yapılmadı" in m



# ------------------------------------------------------------------ anahtar mesajları ve sayaç

def _yanit(kod):
    import httpx2 as httpx
    return httpx.Response(kod, request=httpx.Request("POST", "https://api.anthropic.com/v1/messages"))


class _Reddeden(_SahteAnthropic):
    def _create(self, **kw):
        import anthropic
        raise anthropic.AuthenticationError("invalid x-api-key", response=_yanit(401), body=None)


class _Baglantisiz(_SahteAnthropic):
    def _create(self, **kw):
        import anthropic
        import httpx2 as httpx
        raise anthropic.APIConnectionError(request=httpx.Request("POST", "https://api.anthropic.com/v1/messages"))


def test_gecersiz_ortak_anahtar_ornek_soruda_kayitli_cevap_ve_sakin_not(app, monkeypatch):
    import anthropic
    monkeypatch.setattr(anthropic, "Anthropic", _Reddeden)
    at = app(ANTHROPIC_API_KEY="gecersiz-ortak").run()
    assert "Bu demo kendi Anthropic API anahtarınızla" not in _metinler(at)   # henüz denenmedi
    at.button(key="ornek_0").click().run()
    assert not at.exception
    m = _metinler(at)
    assert "Kayıtlı örnek cevap" in m and "Bu demo kendi Anthropic API anahtarınızla" in m
    assert "Anahtar geçersiz" not in m and not at.error
    at.run()                                              # ret bu çalıştırmada öğrenildi; sonrakinde
    assert at.button(key="sor").disabled                  # ortak anahtar artık kullanılmıyor


def test_ziyaretci_anahtari_reddedilirse_anahtar_gecersiz(app, monkeypatch):
    import anthropic
    monkeypatch.setattr(anthropic, "Anthropic", _Reddeden)
    at = app().run()
    at.text_input(key="ziyaretci_anahtari").input(GIZLI).run()
    at.text_area(key="soru").input("Cayma süresi kaç gün?")
    at.button(key="sor").click().run()
    assert any("Anahtar geçersiz" in str(e.proto.title) for e in at.error)
    assert GIZLI not in _metinler(at)


def test_kimlik_ve_baglanti_hatasi_sayactan_dusmez():
    import anthropic
    import httpx2 as httpx
    req = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    hatalar = [anthropic.AuthenticationError("x", response=httpx.Response(401, request=req), body=None),
               anthropic.APIConnectionError(request=req),
               anthropic.APITimeoutError(request=req)]
    s = GunlukSayac(10)
    for h in hatalar:
        def at(_h=h, **kw):
            raise _h
        ist = SayacliIstemci(SimpleNamespace(messages=SimpleNamespace(create=at),
                                             beta=SimpleNamespace(messages=SimpleNamespace(create=at))), s)
        with pytest.raises(type(h)):
            ist.messages.create(model="x")
        assert ist.cagri_sayisi == 0
    assert s.kalan() == 10


def test_diger_api_hatalari_sayactan_duser():
    import anthropic
    import httpx2 as httpx
    req = httpx.Request("POST", "https://api.anthropic.com/v1/messages")

    def at(**kw):
        raise anthropic.InternalServerError("x", response=httpx.Response(500, request=req), body=None)
    s = GunlukSayac(10)
    ist = SayacliIstemci(SimpleNamespace(messages=SimpleNamespace(create=at),
                                         beta=SimpleNamespace(messages=SimpleNamespace(create=at))), s)
    with pytest.raises(anthropic.InternalServerError):
        ist.messages.create(model="x")
    assert s.kalan() == 9   # model tarafında işlenmiş olabilecek çağrı sayılır


def test_baglanti_hatasinda_arayuz_sayaci_dusmez(app, monkeypatch):
    import anthropic
    monkeypatch.setattr(anthropic, "Anthropic", _Baglantisiz)
    at = app(ANTHROPIC_API_KEY="sahte-ortak").run()
    at.text_area(key="soru").input("Cayma süresi kaç gün?")
    at.button(key="sor").click().run()
    assert not at.exception
    m = _metinler(at)
    assert any("Servise ulaşılamadı" in str(e.proto.title) for e in at.error)
    assert "Bugün kalan ortak çağrı: **300 / 300**" in m



# ------------------------------------------------------------------ yeniden dağıtım ve beklenmeyen hata

def test_guncel_nesne_eski_siniftan_kalani_yeniden_kurar():
    """Canlıdaki hata: yeniden dağıtımdan sonra önbellekte eski GunlukSayac (iade yöntemi yok) kaldı."""
    from mevzuat_rag.arayuz import guncel_nesne

    class EskiSayac:            # eski kodun sınıfı: iade yok
        pass

    kurulan = []

    def getir():
        if not kurulan:
            kurulan.append(EskiSayac())
        return kurulan[-1]

    def temizle():
        kurulan.clear()
        kurulan.append(GunlukSayac(5))
    getir.clear = temizle
    s = guncel_nesne(getir, GunlukSayac)
    assert isinstance(s, GunlukSayac) and hasattr(s, "iade")
    assert guncel_nesne(getir, GunlukSayac) is s          # güncelse dokunulmaz


class _Bozuk(_SahteAnthropic):
    def _create(self, **kw):
        raise RuntimeError("beklenmeyen")


def test_beklenmeyen_hata_iz_kaydi_gostermez(app, monkeypatch):
    import anthropic
    monkeypatch.setattr(anthropic, "Anthropic", _Bozuk)
    at = app(ANTHROPIC_API_KEY="sahte-ortak").run()
    at.text_area(key="soru").input("Cayma süresi kaç gün?")
    at.button(key="sor").click().run()
    assert not at.exception
    assert any("Beklenmeyen hata" in str(e.proto.title) for e in at.error)
    at.button(key="ornek_2").click().run()                 # örnek soruda kayıtlı cevaba düşer
    assert not at.exception and "Kayıtlı örnek cevap" in _metinler(at)
