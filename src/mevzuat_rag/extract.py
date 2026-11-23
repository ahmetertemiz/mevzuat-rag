"""PDF -> satırlar, paragraflar, dipnotlar ve ek bölümü.

Temel fikir: mevzuat.gov.tr PDF'lerinde gövde, dipnot ve dipnot işaretleri farklı puntoda.
  - gövde   : belgedeki en yaygın punto (kanunlarda 12, yönetmelikte 11)
  - dipnot  : gövdeden 1 punto küçük
  - işaret  : çok küçük (6.5-8) üst simge rakamlar, ör. "hükümler⁴⁵"
Bu sayede dipnotlar, sayfa sonunda madde metninin ortasına girse bile ayrılabilir.

Gövdedeki dipnot işaretleri metinden silinmez; "⟨fn:45⟩" belirtecine çevrilir ki parçalama
adımı dipnotu doğru maddeye/fıkraya bağlayabilsin.
"""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

import pymupdf

FN_OPEN, FN_CLOSE = "⟨fn:", "⟩"
FN_TOKEN_RE = re.compile(r"⟨fn:([^⟩]+)⟩")

ARTICLE_HEADER_RE = re.compile(
    r"^(?P<tip>(?:GEÇİCİ|EK)\s+)?MADDE\s+(?P<no>\d+(?:/[A-ZÇĞİÖŞÜ])?)\s*[-–−]\s*(?P<rest>.*)$",
    re.S,
)
YON_FOOTNOTE_START_RE = re.compile(r"^\((\d+)\)\s")


@dataclass
class Line:
    page: int          # 1 tabanlı
    y: float
    x0: float
    size: float        # baskın punto (işaretler hariç)
    text: str          # işaretler ⟨fn:..⟩ olarak gömülü
    first_marker: str | None = None  # satır küçük puntolu bir rakamla başlıyorsa (dipnot numarası)


@dataclass
class Paragraph:
    text: str
    page: int
    x0: float


@dataclass
class Extracted:
    body_size: float
    paragraphs: list[Paragraph]                  # ana metin (ek bölümü hariç)
    footnotes: dict[str, str]                    # dipnot no -> metin
    footnote_pages: dict[str, int]
    appendix_lines: list[Line]                   # ek bölümü (tablolar, listeler, formlar)
    appendix_start_page: int | None
    header_text: str                             # ilk maddeden önceki metin (başlık, RG bilgisi)
    pdf_metadata: dict = field(default_factory=dict)


def _is_heading_like(text: str) -> bool:
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return False
    upper = sum(1 for c in letters if c.isupper())
    return upper / len(letters) > 0.85 and len(text.strip()) >= 2


def _page_lines(page: pymupdf.Page, body_size: float) -> list[Line]:
    """Sayfadaki satırları üretir. Aynı yükseklikteki parçaları (iki yana yaslı satırlarda
    kelimeler ayrı 'line' olarak gelebiliyor) tek satırda birleştirir."""
    raw = []
    for b in page.get_text("dict")["blocks"]:
        for ln in b.get("lines", []):
            spans = [s for s in ln["spans"] if s["text"] != ""]
            if not spans:
                continue
            raw.append((ln["bbox"][1], ln["bbox"][3], ln["bbox"][0], spans))
    raw.sort(key=lambda r: (round(r[0], 0), r[2]))

    groups: list[list] = []
    for r in raw:
        # aynı satır: dikey olarak örtüşüyor (üst simgeler biraz yukarıda olabilir)
        if groups:
            g = groups[-1]
            gy0, gy1 = g[0], g[1]
            overlap = min(gy1, r[1]) - max(gy0, r[0])
            if overlap > 0.5 * min(gy1 - gy0, r[1] - r[0]):
                g[2].append((r[2], r[3]))
                g[0], g[1] = min(gy0, r[0]), max(gy1, r[1])
                continue
        groups.append([r[0], r[1], [(r[2], r[3])]])

    marker_max = body_size - 2.5
    lines: list[Line] = []
    for y0, _y1, parts in groups:
        parts.sort(key=lambda p: p[0])
        spans = [s for _x, sp in parts for s in sp]
        x0 = parts[0][0]
        text_parts: list[str] = []
        sizes: Counter = Counter()
        first_marker = None
        seen_text = False
        for s in spans:
            t = s["text"]
            if s["size"] <= marker_max and t.strip():
                num = t.strip()
                if not seen_text and re.fullmatch(r"\d+", num):
                    first_marker = num  # dipnot satırının başındaki numara
                    continue
                if re.fullmatch(r"\(?\d+\)?", num):
                    text_parts.append(f"{FN_OPEN}{num.strip('()')}{FN_CLOSE}")
                    continue
            if t.strip():
                seen_text = True
                sizes[round(s["size"], 1)] += len(t.strip())
            text_parts.append(t)
        if not sizes:
            continue
        text = re.sub(r"[ \t]+", " ", "".join(text_parts)).strip()
        if not text:
            continue
        size = sizes.most_common(1)[0][0]
        lines.append(Line(page.number + 1, y0, x0, size, text, first_marker))
    return lines


def _doc_body_size(doc: pymupdf.Document) -> float:
    c: Counter = Counter()
    for p in doc:
        for b in p.get_text("dict")["blocks"]:
            for ln in b.get("lines", []):
                for s in ln["spans"]:
                    c[round(s["size"], 1)] += len(s["text"].strip())
    return c.most_common(1)[0][0]


def _find_appendix_start(lines: list[Line], body_size: float) -> int | None:
    """Son maddeden sonra gelen ilk büyük harfli başlık/EK satırının indeksi."""
    last_header = None
    for i, ln in enumerate(lines):
        if ln.size >= body_size - 0.25 and ARTICLE_HEADER_RE.match(ln.text):
            last_header = i
    if last_header is None:
        return None
    for i in range(last_header + 1, len(lines)):
        ln = lines[i]
        if ln.size < body_size - 0.25:
            continue
        t = ln.text.strip()
        if t.startswith("_"):
            continue
        if t == "EK" or t.startswith("Yönetmeliğin Yayımlandığı") or (_is_heading_like(t) and len(t) >= 10):
            return i
    return None


def _is_footnote_start(ln: Line, body_size: float, is_regulation: bool) -> bool:
    # Kanunlarda dipnot satırı küçük puntolu bir numarayla başlar. Bazı sayfalarda dipnot metni
    # gövdeyle aynı puntoda dizilmiş (6563 s.6), bu yüzden burada punto şartı aranmaz.
    if ln.first_marker is not None:
        return True
    return (is_regulation and abs(ln.size - (body_size - 1)) <= 0.3
            and bool(YON_FOOTNOTE_START_RE.match(ln.text)))


def extract(pdf_path: Path, is_regulation: bool = False) -> Extracted:
    doc = pymupdf.open(pdf_path)
    body_size = _doc_body_size(doc)
    foot_size = body_size - 1

    all_lines: list[Line] = []
    for page in doc:
        all_lines.extend(_page_lines(page, body_size))

    app_idx = _find_appendix_start(all_lines, body_size)
    app_page = all_lines[app_idx].page if app_idx is not None else None

    # --- dipnot bölgesini belirle (sayfa bazında) ---
    is_foot = [False] * len(all_lines)
    by_page: dict[int, list[int]] = {}
    for i, ln in enumerate(all_lines):
        by_page.setdefault(ln.page, []).append(i)

    for page_no, idxs in by_page.items():
        start = None
        for i in idxs:
            if _is_footnote_start(all_lines[i], body_size, is_regulation) or all_lines[i].text.startswith("____"):
                start = i
                break
        in_appendix_page = app_page is not None and page_no > app_page
        if start is None and not in_appendix_page:
            # Önceki sayfadan devam eden dipnot: son gövde satırından sonraki dipnot puntolu satırlar
            last_body = max((i for i in idxs if all_lines[i].size >= body_size - 0.25), default=None)
            cand = [i for i in idxs if (last_body is None or i > last_body)
                    and abs(all_lines[i].size - foot_size) <= 0.3]
            if app_idx is not None:
                cand = [i for i in cand if i < app_idx]
            for i in cand:
                is_foot[i] = True
            continue
        if start is not None:
            marker_based = all_lines[start].first_marker is not None
            for i in idxs:
                if i < start:
                    continue
                # Kanun: başlangıçtan sonra sayfanın geri kalanı dipnottur.
                # Yönetmelik: sonnotlardan sonra ek bölümü (RG listesi, form) gelir; punto şartı.
                if marker_based or abs(all_lines[i].size - foot_size) <= 0.3:
                    is_foot[i] = True
            if all_lines[start].text.startswith("____"):
                is_foot[start] = True

    # --- dipnotları topla ---
    footnotes: dict[str, str] = {}
    footnote_pages: dict[str, int] = {}
    current = None
    for i, ln in enumerate(all_lines):
        if not is_foot[i] or ln.text.startswith("____"):
            continue
        num = ln.first_marker
        text = ln.text
        if num is None and is_regulation:
            m = YON_FOOTNOTE_START_RE.match(text)
            if m:
                num, text = m.group(1), text[m.end():]
        if num is not None:
            current = num
            footnotes[current] = text.strip()
            footnote_pages[current] = ln.page
        elif current is not None:
            footnotes[current] = _join(footnotes[current], text)
    footnotes = {k: FN_TOKEN_RE.sub("", v).strip() for k, v in footnotes.items()}

    # --- ana metin satırları -> paragraflar ---
    main_lines = [ln for i, ln in enumerate(all_lines)
                  if not is_foot[i] and (app_idx is None or i < app_idx)
                  and not ln.text.startswith("____")]
    margin = Counter(round(ln.x0) for ln in main_lines).most_common(1)[0][0]

    first_article = next(i for i, ln in enumerate(main_lines) if ARTICLE_HEADER_RE.match(ln.text)
                         or re.match(r"^[A-ZÇĞİÖŞÜ]+ (KISIM|BÖLÜM)$", ln.text))
    # başlık/RG bilgisi ilk KISIM/BÖLÜM ya da maddeden önceki satırlardadır; madde başlığı satırı da
    # bu bölgeye düşebilir, onu paragraflara bırakmak için bir satır geri çekiliyoruz
    header_end = first_article
    if not re.match(r"^[A-ZÇĞİÖŞÜ]+ (KISIM|BÖLÜM)$", main_lines[first_article].text):
        header_end = first_article - 1
    header_text = "\n".join(ln.text for ln in main_lines[:header_end])

    paragraphs: list[Paragraph] = []
    for ln in main_lines[header_end:]:
        new_para = (
            not paragraphs
            or round(ln.x0) > margin + 5
            or ARTICLE_HEADER_RE.match(ln.text)
        )
        if new_para:
            paragraphs.append(Paragraph(ln.text, ln.page, ln.x0))
        else:
            paragraphs[-1].text = _join(paragraphs[-1].text, ln.text)

    appendix_lines = all_lines[app_idx:] if app_idx is not None else []
    appendix_lines = [ln for j, ln in enumerate(appendix_lines) if not is_foot[app_idx + j]] if app_idx is not None else []

    return Extracted(
        body_size=body_size,
        paragraphs=paragraphs,
        footnotes=footnotes,
        footnote_pages=footnote_pages,
        appendix_lines=appendix_lines,
        appendix_start_page=app_page,
        header_text=header_text,
        pdf_metadata=dict(doc.metadata or {}),
    )


def _join(a: str, b: str) -> str:
    """İki satırı birleştirir. Bu PDF'lerde otomatik heceleme yok; satır sonundaki tire gerçek
    bir tiredir ("elektrik-" + "elektronik", "1/7/2022-" + "7416/4 md."). Tire korunur, boşluk konmaz."""
    a = a.rstrip()
    b = b.lstrip()
    if a.endswith("-") and len(a) > 1 and a[-2].isalnum():
        return a + b
    return f"{a} {b}"
