"""Türkçe metin yardımcıları.

Python'un str.lower() fonksiyonu Türkçe'yi bilmez: "I".lower() -> "i" (doğrusu "ı"),
"İ".lower() -> "i̇" (i + birleşik nokta). Bu yüzden küçük/büyük harf dönüşümünü elle yapıyoruz.
"""
from __future__ import annotations


def tr_lower(s: str) -> str:
    return s.replace("I", "ı").replace("İ", "i").lower()


def tr_upper(s: str) -> str:
    return s.replace("i", "İ").replace("ı", "I").upper()


def tr_title(s: str) -> str:
    """'TÜKETİCİNİN KORUNMASI HAKKINDA KANUN' -> 'Tüketicinin Korunması Hakkında Kanun'"""
    out = []
    for w in s.split():
        lw = tr_lower(w)
        if lw in ORDINAL_SUFFIXES and out and out[-1][-1:].isdigit():
            out.append(lw)  # "77 NCİ" -> "77 nci"
            continue
        out.append(tr_upper(lw[:1]) + lw[1:])
    return " ".join(out)


ORDINAL_SUFFIXES = {"nci", "ncı", "ncu", "ncü", "inci", "ıncı", "uncu", "üncü"}


# ------------------------------------------------------------------ BM25 tokenizer
#
# Türkçe eklemeli bir dil: "hakkı / hakkını / hakkının". Kök bulucu yerine kelimenin ilk 5 harfini
# alıyoruz (F5 kırpma; Türkçe bilgi erişiminde literatürde iyi sonuç veren basit yöntem).
# Madde numaraları ise özel belirteçlere çevrilir ki "6502 m.48", "madde 48", "47/A", "Ek 1",
# "Geçici 2" gibi sorgular doğrudan o maddeyi bulsun: md:48, md:47/a, md:ek1, md:gecici2.
#
# Madde belirteçleri yalnızca sorguda ve parçanın bağlam başlığında üretilir. Madde gövdesindeki
# atıflar ("48 inci maddesinin ...") belirtece çevrilmez; aksi hâlde 48. maddeye atıf yapan her
# madde "madde 48" sorgusunda 48. maddenin kendisiyle yarışırdı.

import re  # noqa: E402

PREFIX_LEN = 5
_SUFFIX = r"(?:'?\s*(?:inci|ıncı|uncu|üncü|nci|ncı|ncu|ncü)|\.)?"
_REF_PATTERNS = [
    # "geçici madde 2", "geçici m. 2", "ek madde 1", "ek md.1"
    (re.compile(r"\b(geçici|ek)\s+(?:madde\w*|md\.?|m\.)\s*(\d+)\b"), lambda m: f"md:{_kind(m.group(1))}{m.group(2)}"),
    # "geçici 2", "ek 1"
    (re.compile(r"\b(geçici|ek)\s+(\d+)\b(?!\s*/)"), lambda m: f"md:{_kind(m.group(1))}{m.group(2)}"),
    # "madde 47/a", "m.47/a", "47/a"  (tarih "1/7/2022" eşleşmez: / sonrası harf olmalı)
    (re.compile(r"(?:\b(?:madde\w*|md\.?|m\.)\s*)?\b(\d+)\s*/\s*([a-zçğıöşü])\b"), lambda m: f"md:{m.group(1)}/{m.group(2)}"),
    # "madde 48", "m.48", "m. 48", "md. 48"
    (re.compile(r"\b(?:madde|md\.?|m\.)\s*(\d+)\b"), lambda m: f"md:{m.group(1)}"),
    # "48. madde", "48 inci madde", "48'inci maddesi"
    (re.compile(r"\b(\d+)\s*" + _SUFFIX + r"\s+madde\w*"), lambda m: f"md:{m.group(1)}"),
]


def _kind(w: str) -> str:
    return "gecici" if w.startswith("geç") else "ek"


STOPWORDS = {
    "ve", "veya", "ile", "bu", "şu", "o", "bir", "için", "de", "da", "ki", "mi", "mı", "mu", "mü",
    "ne", "ya", "gibi", "olan", "olarak", "üzere", "en", "daha", "çok", "her", "ama", "fakat",
    "ancak", "ise", "eğer", "kadar", "göre", "ait", "dair", "nasıl", "nedir", "neler", "nelerdir",
    "hangi", "hangileri", "hangileridir", "kaç", "midir", "mıdır", "mudur", "müdür", "var", "yok",
    "ben", "benim", "bana", "beni", "biz", "bizim", "sen", "siz", "onlar", "şey", "diye",
    "miyim", "mıyım", "muyum", "müyüm", "mısınız", "misiniz",
}

_NORMALIZE = str.maketrans({"â": "a", "î": "i", "û": "u", "’": "'", "‘": "'"})
_WORD_RE = re.compile(r"[a-zçğıöşü0-9]+")


def normalize(text: str) -> str:
    return tr_lower(text).translate(_NORMALIZE)


def article_refs(text: str) -> tuple[list[str], str]:
    """Metindeki madde atıflarını belirtece çevirir; (belirteçler, atıfları silinmiş metin) döner."""
    t = normalize(text)
    refs: list[str] = []
    for pat, make in _REF_PATTERNS:
        def repl(m):
            refs.append(make(m))
            return " "
        t = pat.sub(repl, t)
    return refs, t


def word_tokens(text: str) -> list[str]:
    out = []
    for w in _WORD_RE.findall(normalize(text)):
        if w in STOPWORDS:
            continue
        if w.isdigit():
            out.append(w)
        elif len(w) >= 2:
            out.append(w[:PREFIX_LEN])
    return out


# Belge kimliği: "6502 m.48" sorgusunda "6502" kelimesi TKHK parçalarının yarısından fazlasında
# geçtiği için BM25'te ağırlığı neredeyse sıfırdır; KVKK'nın aynı numaralı maddesi kısa diye öne
# geçebilir. Bu yüzden belge + madde birleşik belirteci de üretilir: md:tkhk:48. Yalnızca o maddede
# geçtiği için yüksek ağırlık alır.
DOC_ALIASES = {
    "6502": "tkhk", "tkhk": "tkhk",
    "6563": "etk", "etk": "etk",
    "6698": "kvkk", "kvkk": "kvkk",
    "msy": "msy",
}
_DOC_PHRASES = [(re.compile(r"mesafeli sözleşmeler yönetmeli"), "msy")]


def doc_aliases(text: str) -> set[str]:
    t = normalize(text)
    found = {DOC_ALIASES[w] for w in _WORD_RE.findall(t) if w in DOC_ALIASES}
    found |= {d for pat, d in _DOC_PHRASES if pat.search(t)}
    return found


def _with_doc(refs: list[str], text: str) -> list[str]:
    docs = doc_aliases(text)
    return refs + [f"md:{d}:{r[3:]}" for r in refs for d in sorted(docs)]


def query_tokens(query: str) -> list[str]:
    refs, rest = article_refs(query)
    return _with_doc(refs, query) + word_tokens(rest)


def document_tokens(header: str, body: str) -> list[str]:
    """Bağlam başlığı madde belirteci üretir; gövde üretmez (yukarıdaki açıklamaya bakın)."""
    refs, rest = article_refs(header)
    return _with_doc(refs, header) + word_tokens(rest) + word_tokens(body)
