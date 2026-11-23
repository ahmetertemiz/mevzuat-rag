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


# ------------------------------------------------------------------ birimli sayılar
#
# Süre, tutar ve oranlar birimiyle birlikte eşlenir: "iki yıl" ancak kaynakta 2 YIL olarak geçiyorsa
# tutarlıdır; kaynakta yalnızca "(2)" fıkra numarası ya da "2 gün" varsa tutarsızdır. "otuz gün" ile
# "otuz iş günü" de ayrı birimlerdir.

_BIRIM_KOK = [(re.compile(r"^iş\s+gün"), "iş günü"), (re.compile(r"^gün"), "gün"),
              (re.compile(r"^hafta"), "hafta"), (re.compile(r"^yıl"), "yıl"), (re.compile(r"^saat"), "saat"),
              (re.compile(r"^dakika"), "dakika"), (re.compile(r"^(türk\s+lira|lira|tl)"), "tl"),
              (re.compile(r"^kuruş"), "kuruş"), (re.compile(r"^kat"), "kat"), (re.compile(r"^ay"), "ay")]
_DIGIT_V = r"\d{1,3}(?:\.\d{3})+|\d+"
# Aralık: "2.859-28.620 TL" normalleştirmede "2.859 28.620 tl" olur; iki uç da birimi alır.
_DIGIT_BIRIMLI = re.compile(
    rf"(?P<d1>{_DIGIT_V})(?:\s*(?:-|\s)\s*(?P<d2>{_DIGIT_V}))?(?:'?\w*)?\s+(?P<u>{_UNITS_V}|{_AY_V})\b")
_SPELLED_BIRIMLI = re.compile(rf"\b(?P<n>{_NUMSEQ})\s+(?P<u>{_UNITS_V}|{_AY_V})\b")
_YUZDE = re.compile(rf"(?:%\s*(?P<d>{_DIGIT_V})|\byüzde\s+(?P<dd>{_DIGIT_V})\b|\byüzde\s+(?P<n>{_NUMSEQ})\b)")


def _birim(u: str) -> str:
    for pat, ad in _BIRIM_KOK:
        if pat.match(u):
            return ad
    return u


def _int(tok: str) -> int:
    return int(tok.replace(".", ""))


def birimli_sayilar(text: str) -> set[tuple[int, str]]:
    """Metindeki (değer, birim) çiftleri: '14 gün', 'on dört gün', '2.859-28.620 TL', 'yüzde on'."""
    t = norm(text)
    out: set[tuple[int, str]] = set()
    for m in _DIGIT_BIRIMLI.finditer(t):
        u = _birim(m.group("u"))
        out.add((_int(m.group("d1")), u))
        if m.group("d2"):
            out.add((_int(m.group("d2")), u))
    for m in _SPELLED_BIRIMLI.finditer(t):
        v = tr_sayi(m.group("n"))
        if v is not None:
            out.add((v, _birim(m.group("u"))))
    for m in _YUZDE.finditer(t):
        if m.group("d") or m.group("dd"):
            out.add((_int(m.group("d") or m.group("dd")), "yüzde"))
        else:
            v = tr_sayi(m.group("n"))
            if v is not None:
                out.add((v, "yüzde"))
    return out


def _parca_metin_parcalari(parca: dict, belge: dict | None) -> list[str]:
    parts = parca_metinleri(parca) + [parca.get("baglam_basligi", ""), parca.get("madde_etiketi", "")]
    if belge:
        parts.append(" ".join(str(belge.get(k, "")) for k in ("numara", "tam_ad")))
    return parts


def parca_sayilari(parca: dict, belge: dict | None = None) -> set[int]:
    """Gösterilen parçada geçen sayılar: metin, dipnotlar, mülga kaydı ve parça kimliği
    (madde no, fıkra numaraları, kanun numarası)."""
    vals: set[int] = set()
    for p in _parca_metin_parcalari(parca, belge):
        vals |= sayilar(p)
    vals |= {f for f in parca.get("fikralar") or [] if isinstance(f, int)}
    if parca.get("yil"):
        vals.add(int(parca["yil"]))
    return vals


def sayi_tutarliligi(cumle: str, alintilar: list[str], parcalar: list[dict],
                     belgeler: dict[str, dict] | None = None) -> list[int]:
    """Cümlede geçip alıntılarda ve gösterilen parçalarda geçmeyen sayılar (boşsa tutarlı).

    Birimli sayılar (süre, tutar, oran) aynı değer ve aynı birimle geçmeli; birimsiz sayılar
    (madde/fıkra numarası, tarih, kanun numarası) değer olarak geçmeli."""
    izinli: set[int] = set()
    izinli_birimli: set[tuple[int, str]] = set()
    for a in alintilar:
        izinli |= sayilar(a)
        izinli_birimli |= birimli_sayilar(a)
    for p in parcalar:
        b = (belgeler or {}).get(p.get("belge_id"))
        izinli |= parca_sayilari(p, b)
        for metin in _parca_metin_parcalari(p, b):
            izinli_birimli |= birimli_sayilar(metin)
    cb = birimli_sayilar(cumle)
    hatali = {v for v, u in cb if (v, u) not in izinli_birimli}
    birimli_degerler = {v for v, _ in cb}
    hatali |= {v for v in sayilar(cumle) if v not in birimli_degerler and v not in izinli}
    return sorted(hatali)
