"""Cevap doğrulama: alıntı kontrolü ve sayı tutarlılığı. Model çağrısı yapmaz.

1) Alıntı: modelin her dayanak için verdiği kelimesi kelimesine alıntı, GÖSTERİLEN parça kimliğinin
   metninde (ya da o parçanın dipnotlarında) gerçekten geçmeli. Karşılaştırma normalleştirilmiş
   metin üzerinde yapılır: Unicode NFKC, Türkçe küçük harf, tire türleri ve yumuşak tire boşluğa,
   tırnak türleri tek biçime, boşluklar tek boşluğa. Değişiklik notları ("(Ek:...)") atlanarak
   yapılan alıntılar da kabul edilir.

2) Sayı tutarlılığı: cümlede geçen her süre, tutar, oran, tarih ve madde numarası, o cümlenin
   alıntılarında ya da gösterilen parçanın metninde/kimliğinde de geçmeli. Rakamla ve yazıyla
   yazılmış biçimler aynı değere çevrilir ("14 gün" = "on dört gün", "yüz bin Türk Lirası" = 100000).
   Sayı kelimeleri arama tarafından (rewrite._NUM_WORDS) yeniden kullanılır;
   arama modülleri değiştirilmez.
"""
from __future__ import annotations

import re
import unicodedata

from .chunk import strip_amendments
from .rewrite import _NUM_WORDS  # arama tarafındaki sayı kelimeleri (değiştirilmeden)
from .textnorm import tr_lower

MIN_ALINTI_KELIME = 3
MAX_ALINTI_KELIME = 40

_DASHES = re.compile(r"[­‐‑‒–—―−-]")
_QUOTES = str.maketrans({"“": '"', "”": '"', "„": '"', "″": '"', "‘": "'", "’": "'", "‚": "'", "′": "'"})
_EDGE_PUNCT = " .,;:!?…\"'()[]«»"


def norm(text: str) -> str:
    t = unicodedata.normalize("NFKC", text)
    t = tr_lower(t).translate(_QUOTES)
    t = _DASHES.sub(" ", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def norm_alinti(text: str) -> str:
    return norm(text).strip(_EDGE_PUNCT).strip()


# ------------------------------------------------------------------ alıntı

def parca_metinleri(parca: dict) -> list[str]:
    """Bir parçada alıntının aranacağı metinler."""
    out = [parca["metin"], strip_amendments(parca["metin"])]
    out += [d["metin"] for d in parca.get("dipnotlar") or []]
    if parca.get("mulga"):
        out.append(parca["mulga"].get("ham", ""))
    return out


def alinti_dogrula(alinti: str, parca: dict | None) -> tuple[bool, str]:
    if parca is None:
        return False, "parça bağlamda yok"
    a = norm_alinti(alinti)
    n = len(a.split())
    if n < MIN_ALINTI_KELIME:
        return False, f"alıntı çok kısa ({n} kelime)"
    if n > MAX_ALINTI_KELIME:
        return False, f"alıntı çok uzun ({n} kelime)"
    for h in parca_metinleri(parca):
        if a in norm(h):
            return True, ""
    return False, "alıntı parçada geçmiyor"


# ------------------------------------------------------------------ sayılar

_BIRLER = {"bir": 1, "iki": 2, "üç": 3, "dört": 4, "beş": 5, "altı": 6, "yedi": 7, "sekiz": 8, "dokuz": 9}
_ONLAR = {"on": 10, "yirmi": 20, "otuz": 30, "kırk": 40, "elli": 50, "altmış": 60, "yetmiş": 70,
          "seksen": 80, "doksan": 90}
_BUYUK = {"bin": 1_000, "milyon": 1_000_000, "milyar": 1_000_000_000}

# Arama tarafının birim listesine ek olarak tutarlarda "türk lirası" ve katlar ("on katı").
# Birimler her eki alabilir ("gündür", "günlüktür", "yıllık"); yalnız "ay" kısa ve "ayıp" gibi
# kelimelerle karışabileceği için sayılı ek listesiyle eşlenir.
_UNITS_V = r"(?:iş\s+günü|gün|hafta|yıl|saat|dakika|türk\s+lirası|lira|tl|kuruş|kat)\w*"
_AY_V = r"ay(?:lık|lık|da|dan|ı|a|dır|lıktır|dır)?"
_NUMSEQ = rf"(?:(?:{_NUM_WORDS})\s+)*(?:{_NUM_WORDS})"
_SPELLED_V = re.compile(
    rf"\b(?P<n>{_NUMSEQ})\s+(?:{_UNITS_V}|{_AY_V})\b|\byüzde\s+(?P<p>{_NUMSEQ})\b")
# Aramadaki rewrite._DIGITS (\d+) tutarları parçalar ("1.987.014" -> 1, 987, 14); burada binlik
# noktalı tutarlar tek değer olarak okunur.
_DIGIT_NUM = re.compile(r"\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:,\d+)?")


def tr_sayi(kelimeler: str) -> int | None:
    """'on dört' -> 14, 'yüz bin' -> 100000, 'iki yüz elli bin' -> 250000, 'bin' -> 1000."""
    total, current = 0, 0
    for w in kelimeler.split():
        if w in _BIRLER:
            current += _BIRLER[w]
        elif w in _ONLAR:
            current += _ONLAR[w]
        elif w == "yüz":
            current = (current or 1) * 100
        elif w in _BUYUK:
            total += (current or 1) * _BUYUK[w]
            current = 0
        else:
            return None
    return total + current


def sayilar(text: str) -> set[int]:
    """Metindeki rakamla ya da yazıyla (birimli) yazılmış sayıların değerleri."""
    t = norm(text)
    vals: set[int] = set()
    for m in _DIGIT_NUM.finditer(t):
        tok = m.group(0).split(",")[0].replace(".", "")
        vals.add(int(tok))
    for m in _SPELLED_V.finditer(t):
        v = tr_sayi(m.group("n") or m.group("p"))
        if v is not None:
            vals.add(v)
    return vals


def parca_sayilari(parca: dict, belge: dict | None = None) -> set[int]:
    """Gösterilen parçada geçen sayılar: metin, dipnotlar, mülga kaydı ve parça kimliği
    (madde no, fıkra numaraları, kanun numarası)."""
    parts = parca_metinleri(parca) + [parca.get("baglam_basligi", ""), parca.get("madde_etiketi", "")]
    vals: set[int] = set()
    for p in parts:
        vals |= sayilar(p)
    vals |= {f for f in parca.get("fikralar") or [] if isinstance(f, int)}
    if parca.get("yil"):
        vals.add(int(parca["yil"]))
    if belge:
        vals |= sayilar(" ".join(str(belge.get(k, "")) for k in ("numara", "tam_ad")))
    return vals


def sayi_tutarliligi(cumle: str, alintilar: list[str], parcalar: list[dict],
                     belgeler: dict[str, dict] | None = None) -> list[int]:
    """Cümlede geçip alıntılarda ve gösterilen parçalarda geçmeyen sayılar (boşsa tutarlı)."""
    izinli: set[int] = set()
    for a in alintilar:
        izinli |= sayilar(a)
    for p in parcalar:
        izinli |= parca_sayilari(p, (belgeler or {}).get(p.get("belge_id")))
    return sorted(v for v in sayilar(cumle) if v not in izinli)
