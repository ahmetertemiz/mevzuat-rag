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
