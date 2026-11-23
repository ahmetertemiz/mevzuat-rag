"""Arayüzün (streamlit_app.py) Streamlit'e bağlı olmayan mantığı; ayrı tutuldu ki pytest ile sınansın.

- kisa_atif / fikra_bul: cümle yanındaki kaynak etiketi ("6502 m.24/1")
- madde_tam_metni: bir maddenin bütün parçalarını birleştirir
- GunlukSayac: bellekte, süreç başına günlük model çağrısı sayacı (UTC gününe göre sıfırlanır)
- SayacliIstemci: anthropic istemcisini sarar; her messages.create çağrısından önce sayaçtan pay alır
- cevaplayici_kur: arama modüllerini değiştirmeden, verilen istemciyle çalışan bir Cevaplayici kurar
"""
from __future__ import annotations

import datetime as dt
import re
import threading
from types import SimpleNamespace

from .verify import norm, norm_alinti, strip_amendments

VARSAYILAN_GUNLUK_SINIR = 300   # soru başına 2 çağrı (yeniden yazım + cevap), JSON okunamazsa 3


# ------------------------------------------------------------------ atıf

_FIKRA = re.compile(r"(?m)^\s*\((\d+)\)")


def fikra_bul(parca: dict, alinti: str) -> str | None:
    """Alıntının geçtiği fıkra numarası; dipnottaysa "dipnot"; bulunamazsa None."""
    a = norm_alinti(alinti or "")
    if not a:
        return None
    metin = parca.get("metin") or ""
    sinirlar = [(m.start(), m.group(1)) for m in _FIKRA.finditer(metin)]
    for i, (bas, no) in enumerate(sinirlar):
        son = sinirlar[i + 1][0] if i + 1 < len(sinirlar) else len(metin)
        parcacik = metin[bas:son]
        if a in norm(parcacik) or a in norm(strip_amendments(parcacik)):
            return no
    if any(a in norm(d.get("metin", "")) for d in parca.get("dipnotlar") or []):
        return "dipnot"
    return None


def belge_etiketi(parca: dict, belgeler: dict[str, dict]) -> str:
    """Kanunlar numarasıyla (6502), yönetmelik kısaltmasıyla (MSY)."""
    b = belgeler.get(parca.get("belge_id", ""), {})
    if b.get("tur") == "kanun" and b.get("numara"):
        return b["numara"]
    return parca.get("belge_kisa_ad") or b.get("kisa_ad") or "?"


def kisa_atif(parca: dict, belgeler: dict[str, dict], alinti: str | None = None) -> str:
    """'6502 m.24/1', 'MSY m.12/A', '6502 m.12, dipnot', '6502 ceza tablosu (2026)'."""
    bel = belge_etiketi(parca, belgeler)
    if parca.get("tur") == "tablo":
        return f"{bel} ceza tablosu ({parca.get('yil')})"
    etiket = (parca.get("madde_etiketi") or f"Madde {parca.get('madde_no')}")
    ek = bool(re.match(r"^\s*Ek\s", etiket, flags=re.IGNORECASE))
    no = re.sub(r"^\s*(Ek\s+)?(Geçici\s+)?Madde\s*", "", etiket, flags=re.IGNORECASE).strip()
    gecici = bool(re.search(r"Geçici\s+Madde", etiket, flags=re.IGNORECASE))
    atif = f"{bel} {'ek ' if ek else ''}{'geç. ' if gecici else ''}m.{no}"
    f = fikra_bul(parca, alinti) if alinti else None
    if f == "dipnot":
        atif += ", dipnot"
    elif f:
        atif += f", f.{f}" if "/" in no else f"/{f}"   # "m.12/A, f.3" ama "m.24/1"
    return atif


def madde_tam_metni(parca: dict, tum_parcalar: list[dict]) -> str:
    """Maddenin bütün parçaları sırayla (madde birden çok parçaya bölündüyse hepsi)."""
    if parca.get("tur") == "tablo":
        return parca.get("metin", "")
    ayni = [p for p in tum_parcalar
            if p.get("belge_id") == parca.get("belge_id") and p.get("madde_no") == parca.get("madde_no")
            and p.get("tur") != "tablo"]
    ayni.sort(key=lambda p: p.get("parca") or 0)
    return "\n".join(p.get("metin", "").strip() for p in ayni) or parca.get("metin", "")


# ------------------------------------------------------------------ günlük sınır

class SinirAsildi(RuntimeError):
    pass


class GunlukSayac:
    """Süreç belleğinde tutulan günlük çağrı sayacı. Sunucu yeniden başlarsa sıfırlanır; birden çok
    süreç/kopya çalışıyorsa her biri kendi sayacını tutar (README'de belirtildi)."""

    def __init__(self, sinir: int, saat=None):
        self.sinir = sinir
        self._saat = saat or (lambda: dt.datetime.now(dt.timezone.utc).date())
        self._kilit = threading.Lock()
        self._gun = self._saat()
        self._sayi = 0

    def _gun_kontrol(self) -> None:
        bugun = self._saat()
        if bugun != self._gun:
            self._gun, self._sayi = bugun, 0

    def kalan(self) -> int:
        with self._kilit:
            self._gun_kontrol()
            return max(0, self.sinir - self._sayi)

    def kullanilan(self) -> int:
        with self._kilit:
            self._gun_kontrol()
            return self._sayi

    def al(self) -> None:
        """Bir çağrı hakkı ayırır; kalmadıysa SinirAsildi."""
        with self._kilit:
            self._gun_kontrol()
            if self._sayi >= self.sinir:
                raise SinirAsildi("Günlük model çağrısı sınırına ulaşıldı.")
            self._sayi += 1


class SayacliIstemci:
    """anthropic.Anthropic'i sarar: messages.create ve beta.messages.create her çağrıda sayaçtan pay
    alır (sayac None ise sayılmaz: ziyaretçinin kendi anahtarı). SDK'nın kendi ağ yeniden denemeleri
    tek çağrı sayılır."""

    def __init__(self, istemci, sayac: GunlukSayac | None):
        self._istemci, self._sayac = istemci, sayac
        self.cagri_sayisi = 0
        self.messages = SimpleNamespace(create=self._sar(istemci.messages.create))
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._sar(istemci.beta.messages.create)))

    def _sar(self, fn):
        def create(**kw):
            if self._sayac is not None:
                self._sayac.al()
            self.cagri_sayisi += 1
            return fn(**kw)
        return create


# ------------------------------------------------------------------ kurulum

def yeniden_yazici_kur(istemci):
    """QueryRewriter'ı ortam değişkenine dokunmadan verilen istemciyle kurar (ziyaretçi anahtarı süreç
    ortamına yazılmamalı: diğer kullanıcılara sızar). rewrite.py değiştirilmedi; özniteliklerin
    yapıcıyla aynı kaldığı test_arayuz.py'de denetlenir."""
    from .rewrite import PROMPT_VERSION, REWRITE_EFFORT, REWRITE_MODEL, QueryRewriter, sistem_promptu

    rw = QueryRewriter.__new__(QueryRewriter)
    rw.client = istemci
    rw.model, rw.effort, rw.prompt_surumu = REWRITE_MODEL, REWRITE_EFFORT, PROMPT_VERSION
    rw.system = sistem_promptu(PROMPT_VERSION)
    return rw


def cevaplayici_kur(retriever, istemci):
    """Dondurulmuş varsayılan hat (BM25 + yeniden yazım) ve varsayılan cevap modeliyle Cevaplayici."""
    from .answer import Cevaplayici
    from .pipeline import Arayici

    arayici = Arayici(retriever=retriever, rewriter=yeniden_yazici_kur(istemci))
    return Cevaplayici(arayici=arayici, client=istemci)


# ------------------------------------------------------------------ kayıtlı örnek cevaplar

def ornek_cevaplar_yolu():
    from . import config
    return config.ROOT / "data" / "ornek_cevaplar.json"


def cevap_yukle(d: dict):
    """cevap_sozlugu() çıktısını yeniden Cevap nesnesine çevirir; kayıtlı ve canlı cevap aynı arayüz
    koduyla çizilsin diye."""
    from dataclasses import fields

    from .answer import Cevap, Cumle

    adlar = {f.name for f in fields(Cevap)}
    x = {k: v for k, v in d.items() if k in adlar}
    x["cumleler"] = [Cumle(**c) for c in d.get("cumleler") or []]
    x["cikarilan_cumleler"] = [Cumle(**c) for c in d.get("cikarilan_cumleler") or []]
    return Cevap(**x)


def ornek_cevaplari_oku(yol=None) -> dict:
    """{"uretim_tarihi", "model", "yeniden_yazim_modeli", "cevaplar": {soru: {"cevap": dict, "cagri": n}}};
    dosya yoksa boş sözlük."""
    import json

    yol = yol or ornek_cevaplar_yolu()
    try:
        return json.loads(yol.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
