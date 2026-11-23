"""Paragraflar -> maddeler -> parçalar (chunk).

Akış:
  1. Paragrafları dolaşıp KISIM/BÖLÜM başlıklarını, madde başlıklarını ve "MADDE n –"
     satırlarını tanı; her maddenin paragraflarını topla.
  2. Madde içinde fıkraları "(1)", "(2)" ile; fıkra içinde bentleri "a)", "ç)" ile ayır.
  3. Madde kısa ise tek parça. Uzunsa ardışık fıkraları sınıra kadar grupla; tek bir fıkra
     bile uzunsa bent sınırından böl ve fıkranın giriş cümlesini her parçaya ekle.
  4. Dipnot işaretlerini (⟨fn:n⟩) bulunduğu yere göre (başlık/fıkra) parçaya bağla, metinden sil.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .extract import ARTICLE_HEADER_RE, FN_TOKEN_RE, Paragraph
from .textnorm import tr_title

SECTION_RE = re.compile(r"^(?P<sira>[A-ZÇĞİÖŞÜ]+)\s+(?P<tip>KISIM|BÖLÜM)$")
FIKRA_RE = re.compile(r"^\((\d+)\)\s*")
BENT_RE = re.compile(r"^([a-zçğıöşü])\)\s+")
ALT_BENT_RE = re.compile(r"^(\d+)\)\s+")

# Değişiklik notu: (Ek:1/7/2022-7416/2 md.), (Başlığı ile Birlikte Değişik:...),
# (Değişik ibare:RG-23/8/2022-31932), (Değişik: 2/1/2017-KHK-684/8 md.; Aynen kabul: ...)
AMEND_RE = re.compile(
    r"\(\s*(?:Başlığı ile [Bb]irlikte\s+)?(?:Değişik|Ek|Mülga|İptal)[^():]*:[^()]*?\d{1,2}/\d{1,2}/\d{4}[^()]*\)"
)
MULGA_RE = re.compile(r"\(\s*Mülga\s*:\s*(?P<rg>RG-)?(?P<tarih>\d{1,2}/\d{1,2}/\d{4})-(?P<dayanak>[^)]*)\)")

ORDINALS = {1: "birinci", 2: "ikinci", 3: "üçüncü", 4: "dördüncü", 5: "beşinci"}


@dataclass
class Fikra:
    no: int | None
    paras: list[str]                    # ilk paragraf fıkra numarasıyla başlar
    pages: set[int] = field(default_factory=set)


@dataclass
class Article:
    madde_no: str                        # "48", "47/A", "Ek 1", "Geçici 2"
    madde_etiketi: str                   # "Madde 48", "Ek Madde 1", "Geçici Madde 2"
    baslik: str | None
    baslik_fn: list[str]
    kisim: str | None
    bolum: str | None
    intro: str                           # MADDE satırında fıkradan önce kalan metin (ör. değişiklik notu)
    fikralar: list[Fikra]
    pages: set[int]


# ---------------------------------------------------------------- ayrıştırma

def _is_title_candidate(text: str) -> bool:
    t = FN_TOKEN_RE.sub("", text).strip()
    if not t or len(t.split()) > 12:
        return False
    if t[-1] in ".;:," or FIKRA_RE.match(t) or BENT_RE.match(t) or ALT_BENT_RE.match(t):
        return False
    return t[0].isupper()


def parse_articles(paragraphs: list[Paragraph]) -> list[Article]:
    articles: list[Article] = []
    kisim = bolum = None
    pending_section: str | None = None   # "KISIM" / "BÖLÜM" başlığından sonra adı bekleniyor
    cur: Article | None = None
    cur_paras: list[tuple[str, int]] = []
    orphan: list[tuple[str, int]] = []    # ilk maddeden önceki paragraflar (başlık adayı)

    def close():
        nonlocal cur, cur_paras
        if cur is not None:
            _fill_fikralar(cur, cur_paras)
            articles.append(cur)
        cur, cur_paras = None, []

    for p in paragraphs:
        text = p.text.strip()
        sm = SECTION_RE.match(text)
        if sm:
            pending_section = tr_title(f"{sm.group('sira')} {sm.group('tip')}")
            # başlık adayı bir önceki maddenin son paragrafı olamaz; burada bir şey yapmaya gerek yok
            continue
        if pending_section is not None:
            name = f"{pending_section}: {text}"
            if "Kısım" in pending_section:
                kisim, bolum = name, None
            else:
                bolum = name
            pending_section = None
            continue

        hm = ARTICLE_HEADER_RE.match(text)
        if hm:
            # başlık = bir önceki paragraf (başlık gibi görünüyorsa)
            pool = cur_paras if cur is not None else orphan
            baslik = None
            if pool and _is_title_candidate(pool[-1][0]):
                baslik = pool.pop()[0]
            close()
            tip = (hm.group("tip") or "").strip()
            no = hm.group("no")
            if tip == "EK":
                madde_no, etiket = f"Ek {no}", f"Ek Madde {no}"
            elif tip == "GEÇİCİ":
                madde_no, etiket = f"Geçici {no}", f"Geçici Madde {no}"
            else:
                madde_no, etiket = no, f"Madde {no}"
            baslik_fn = FN_TOKEN_RE.findall(baslik) if baslik else []
            cur = Article(
                madde_no=madde_no, madde_etiketi=etiket,
                baslik=FN_TOKEN_RE.sub("", baslik).strip() if baslik else None,
                baslik_fn=baslik_fn, kisim=kisim, bolum=bolum,
                intro="", fikralar=[], pages={p.page},
            )
            rest = hm.group("rest").strip()
            cur_paras = [(rest, p.page)] if rest else []
            continue

        if cur is None:
            orphan.append((text, p.page))
        else:
            cur_paras.append((text, p.page))
            cur.pages.add(p.page)
    close()
    return articles


def _fill_fikralar(a: Article, paras: list[tuple[str, int]]) -> None:
    intro_parts: list[str] = []
    fikralar: list[Fikra] = []
    for text, page in paras:
        # MADDE satırının geri kalanı "(Değişik:...) (1) ..." gibi başlayabilir
        if not fikralar and not FIKRA_RE.match(text):
            while True:
                m = AMEND_RE.match(text) or re.match(r"⟨fn:[^⟩]+⟩", text)
                if not m:
                    break
                intro_parts.append(m.group(0))
                text = text[m.end():].lstrip()
            if not text:
                continue
        fm = FIKRA_RE.match(text)
        if fm:
            fikralar.append(Fikra(int(fm.group(1)), [text], {page}))
        elif fikralar:
            fikralar[-1].paras.append(text)
            fikralar[-1].pages.add(page)
        else:
            # numarasız fıkra (ör. tek fıkralı eski maddeler) ya da giriş
            fikralar.append(Fikra(None, [text], {page}))
    a.intro = " ".join(intro_parts)
    a.fikralar = fikralar


# ---------------------------------------------------------------- yardımcılar

def words(text: str) -> int:
    return len(FN_TOKEN_RE.sub("", text).split())


def strip_amendments(text: str) -> str:
    return re.sub(r"\s{2,}", " ", AMEND_RE.sub("", text)).strip()


def find_amendments(text: str) -> list[str]:
    return [m.group(0) for m in AMEND_RE.finditer(text)]


def segment_markers(raw: str, known: set[str]) -> list[str]:
    """Üst simgeler bitişik gelebilir: '252627' -> ['25','26','27'], '45' -> ['4','5']."""
    if raw in known:
        return [raw]

    def rec(s: str) -> list[str] | None:
        if not s:
            return []
        for n in (3, 2, 1):  # önce uzun: '252627' -> 25,26,27 (2,5,2,... değil)
            head = s[:n]
            if head in known:
                tail = rec(s[n:])
                if tail is not None:
                    return [head] + tail
        return None

    return rec(raw) or [raw]


def classify_footnote(text: str) -> str:
    if "Anayasa Mahkemesi" in text:
        return "aym_karari"
    if re.search(r"[Tt]abloya bakınız|[Tt]abloya bakın", text):
        return "tablo_atfi"
    if "yürürlüğe girer" in text:
        return "yururluk"
    if re.search(r"bakınız", text):
        return "atif"
    return "degisiklik_gecmisi"


# ---------------------------------------------------------------- parçalama

@dataclass
class Piece:
    fikra_nos: list[int | None]
    bentler: list[str] | None
    text_parts: list[str]           # gösterim metninin paragrafları (⟨fn⟩ belirteçleri dahil)
    pages: set[int]


def _split_fikra_by_bent(f: Fikra, max_words: int) -> list[Piece]:
    """Uzun bir fıkrayı bent sınırından böler. Giriş (bentlerden önceki kısım) her parçanın
    başına, kapanış (son bentten sonra gelen 'ifade eder.' gibi kısım) son parçaya eklenir."""
    lead: list[str] = []
    bents: list[tuple[str, list[str]]] = []
    closing: list[str] = []
    for i, para in enumerate(f.paras):
        bm = BENT_RE.match(para)
        if i > 0 and bm:
            bents.append((bm.group(1), [para]))
        elif bents and ALT_BENT_RE.match(para):
            bents[-1][1].append(para)
        elif bents:
            # bentten sonra etiketsiz paragraf: önceki bendin devamı mı, kapanış mı?
            # Kapanış genelde kısa ve küçük harfle başlar ("ifade eder.", "idari para cezası verilir.")
            if len(para.split()) <= 12 and para[:1].islower():
                closing.append(para)
            else:
                bents[-1][1].append(para)
        else:
            lead.append(para)
    if not bents:
        return _split_by_sentences(f, max_words)

    lead_text = " ".join(lead)
    pieces: list[Piece] = []
    cur: list[tuple[str, list[str]]] = []
    budget = max(max_words - words(lead_text), max_words // 2)
    for b in bents:
        bw = sum(words(x) for x in b[1])
        if cur and sum(words(x) for _, ps in cur for x in ps) + bw > budget:
            pieces.append(cur_piece(f, lead, cur, first=not pieces))
            cur = []
        cur.append(b)
    if cur:
        pieces.append(cur_piece(f, lead, cur, first=not pieces))
    if closing:
        pieces[-1].text_parts.extend(closing)
    return pieces


def cur_piece(f: Fikra, lead: list[str], bents: list[tuple[str, list[str]]], first: bool) -> Piece:
    parts = list(lead) if first else [_lead_reminder(lead)]
    for _, ps in bents:
        parts.extend(ps)
    return Piece([f.no], [b for b, _ in bents], parts, set(f.pages))


def _lead_reminder(lead: list[str]) -> str:
    """Devam parçalarında fıkranın giriş cümlesini bağlam için tekrar eder."""
    text = " ".join(lead)
    return f"{text} […]"


def _split_by_sentences(f: Fikra, max_words: int) -> list[Piece]:
    text = " ".join(f.paras)
    sents = re.split(r"(?<=[.;])\s+(?=[A-ZÇĞİÖŞÜ(])", text)
    pieces: list[Piece] = []
    cur: list[str] = []
    for s in sents:
        if cur and words(" ".join(cur + [s])) > max_words:
            pieces.append(Piece([f.no], None, [" ".join(cur)], set(f.pages)))
            cur = []
        cur.append(s)
    if cur:
        pieces.append(Piece([f.no], None, [" ".join(cur)], set(f.pages)))
    return pieces


def split_article(a: Article, max_words: int) -> list[Piece]:
    total = sum(words(p) for f in a.fikralar for p in f.paras)
    if total <= max_words:
        pages = set().union(*(f.pages for f in a.fikralar)) if a.fikralar else set(a.pages)
        return [Piece([f.no for f in a.fikralar], None, [p for f in a.fikralar for p in f.paras], pages)]

    pieces: list[Piece] = []
    group: list[Fikra] = []

    def flush():
        if group:
            pieces.append(Piece([f.no for f in group], None,
                                [p for f in group for p in f.paras],
                                set().union(*(f.pages for f in group))))
            group.clear()

    for f in a.fikralar:
        fw = sum(words(p) for p in f.paras)
        if fw > max_words:
            flush()
            pieces.extend(_split_fikra_by_bent(f, max_words))
            continue
        if group and sum(words(p) for g in group for p in g.paras) + fw > max_words:
            flush()
        group.append(f)
    flush()
    return pieces
