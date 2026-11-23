"""Belge sonundaki idari para cezası tablolarının çıkarılması.

Metin katmanında bu tablolar sütun sırası bozuk çıkıyor (pdftotext'te 6563 tablosunun bent
etiketleri ile tutarlar kayıyor). Bu yüzden PyMuPDF'in tablo algılayıcısını kullanıp her hücrenin
metnini hücre kutusundan (clip) okuyoruz. Birleştirilmiş hücreler None döner; bunları bir üstteki
satırdan devralıyoruz.

Doğrulama iki yönlü:
  1. Otomatik: tablo hücrelerinden okunan sayılar ile aynı bölgedeki ham kelimelerden okunan sayılar
     aynı çoklu küme mi?
  2. Görsel: tablo sayfalarının PNG'si rapora eklenir; insan onayı olmadan tablo indekse girmez.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import pymupdf

from .textnorm import tr_title

AMOUNT_RE = re.compile(r"\d{1,3}(?:\.\d{3})+|\d+")
LIST_HEADING = "DEĞİŞİKLİK GETİREN"


@dataclass
class TableRow:
    bolum: str            # "guncel" | "gecici_madde_3_oncesi" vb.
    fikra: str            # "Birinci fıkrasındaki ceza miktarı"
    bent: str | None
    alt_bent: str | None
    tutar: str            # hücredeki ham değer: "3.973", "2.859-14.309", "En az 28.620"
    sayfa: int


@dataclass
class PenaltyTable:
    baslik: str
    aciklama: str
    yil: int | None
    sayfalar: list[int]
    satirlar: list[TableRow] = field(default_factory=list)
    hucre_sayilari: list[str] = field(default_factory=list)
    ham_sayilar: list[str] = field(default_factory=list)


def _cell_text(page: pymupdf.Page, rect) -> str:
    return " ".join(page.get_text("text", clip=rect).split())


def extract_penalty_table(pdf_path: Path, start_page: int, intro_text: str) -> PenaltyTable | None:
    """start_page (1 tabanlı): ek bölümünün başladığı sayfa. intro_text: ek bölümünde tablodan
    önce gelen gövde metni (başlık + açıklama), extract.py'nin ek satırlarından gelir."""
    doc = pymupdf.open(pdf_path)
    pages: list[int] = []
    for i in range(start_page - 1, len(doc)):
        page = doc[i]
        if LIST_HEADING in page.get_text() and not pages:
            continue
        tabs = [t for t in page.find_tables().tables
                if any("fıkra" in (_cell_text(page, c) if c else "") for r in t.rows[:3] for c in r.cells)]
        if not tabs:
            if pages:
                break
            continue
        pages.append(i)
        if LIST_HEADING in page.get_text():
            break
    if not pages:
        return None

    pre_text = " ".join(intro_text.split())
    title_m = re.search(r"(\d{4} SAYILI .*?TABLO)", pre_text)
    baslik = tr_title(title_m.group(1)) if title_m else ""
    aciklama = pre_text[title_m.end():].strip() if title_m else pre_text
    aciklama = re.split(r"\s\d{4} sayılı Kanunun \d+ n?[cıiuü]+ maddesinin;", aciklama)[0].strip()
    yil_m = re.search(r"(\d{4}) YILINDA", pre_text) or re.search(r"(\d{4}) Yılında", aciklama)         or re.search(r"1/1/(\d{4})", aciklama)
    table = PenaltyTable(baslik=baslik, aciklama=aciklama, yil=int(yil_m.group(1)) if yil_m else None,
                         sayfalar=[p + 1 for p in pages])

    bolum = "guncel"
    last = {"fikra": None, "bent": None, "alt": None}
    for pi in pages:
        page = doc[pi]
        for t in page.find_tables().tables:
            # ham sayılar: tablo bölgesindeki kelimelerden, hücre yapısından bağımsız
            words = page.get_text("words", clip=t.bbox)
            for row in t.rows:
                cells = [None if c is None else _cell_text(page, c) for c in row.cells]
                label, value = cells[0], cells[-1]
                mids = cells[1:-1]
                if value == "TL":
                    if label and "Geçici Madde 3" in label:
                        bolum = "gecici_madde_3_oncesi"
                    continue
                bent = next((m for m in mids if m and "bendi" in m), None)
                alt = next((m for m in mids if m and "alt bent" in m), None)
                if label:  # yeni fıkra satırı
                    last = {"fikra": label, "bent": bent, "alt": alt}
                else:      # birleştirilmiş hücre: üst satırdan devral
                    if bent:
                        last["bent"], last["alt"] = bent, alt
                    elif alt:
                        last["alt"] = alt
                table.satirlar.append(TableRow(bolum, last["fikra"], last["bent"], last["alt"],
                                               value or "", pi + 1))
                table.hucre_sayilari += AMOUNT_RE.findall(value or "")
            # ham sayılar arasından başlık satırlarındaki tarih/sayı vb. ayıklanır: yalnızca
            # tutar sütunundaki kelimeler (tablonun sağ sütunu)
            right_x = t.rows[0].cells[-1][0] if t.rows and t.rows[0].cells[-1] else t.bbox[0]
            for w in words:
                if w[0] >= right_x - 1:
                    table.ham_sayilar += AMOUNT_RE.findall(w[4])
    return table


def table_to_text(t: PenaltyTable, kanun_no: str, madde: str) -> str:
    """Tabloyu okunabilir satırlara çevirir. Aynı hücreye ait birden çok tutar '; ' ile birleşir."""
    lines = [t.baslik]
    if t.aciklama:
        lines.append(t.aciklama)
    groups: list[tuple[tuple, list[str]]] = []
    for r in t.satirlar:
        key = (r.bolum, r.fikra, r.bent, r.alt_bent)
        if groups and groups[-1][0] == key:
            groups[-1][1].append(r.tutar)
        else:
            groups.append((key, [r.tutar]))
    cur_bolum = None
    for (bolum, fikra, bent, alt), vals in groups:
        if bolum != cur_bolum:
            cur_bolum = bolum
            if bolum == "gecici_madde_3_oncesi":
                lines.append(f"Geçici Madde 3 kapsamında, {madde} maddenin değişiklik öncesi hâline göre:")
        label = " ".join(x for x in (fikra, bent, alt) if x)
        lines.append(f"- {label}: " + "; ".join(f"{v} TL" for v in vals))
    return "\n".join(lines)
