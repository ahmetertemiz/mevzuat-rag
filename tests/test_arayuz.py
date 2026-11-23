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
    assert "Ortak anahtar tanımlı değil" in _metinler(at)


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
