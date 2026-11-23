"""Belge -> parça kayıtları (JSONL satırları) + belge üstverisi + tanılama bilgisi."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date

import pymupdf

from . import chunk as ch
from . import tables as tb
from .config import MAX_CHUNK_WORDS, DOCS_RAW, DocSpec
from .extract import ARTICLE_HEADER_RE, FN_TOKEN_RE, extract
from .textnorm import tr_title

DATE_RE = re.compile(r"(\d{1,2})/(\d{1,2})/(\d{4})")


@dataclass
class DocResult:
    meta: dict
    chunks: list[dict]
    diag: dict = field(default_factory=dict)
    table: tb.PenaltyTable | None = None


# ---------------------------------------------------------------- yardımcılar

def _iso(d: str) -> str:
    m = DATE_RE.search(d)
    if not m:
        return d
    return date(int(m.group(3)), int(m.group(2)), int(m.group(1))).isoformat()


def _slug(madde_no: str) -> str:
    s = madde_no.lower().replace("geçici", "gecici").replace(" ", "").replace("/", "")
    return s if s[0].isalpha() else f"m{s}"


def _pdf_date(raw: str) -> str | None:
    m = re.match(r"D:(\d{4})(\d{2})(\d{2})", raw or "")
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else None


def _parse_header(spec: DocSpec, header_text: str) -> dict:
    lines = [ln.strip() for ln in header_text.splitlines() if ln.strip()]
    title_lines = []
    for ln in lines:
        if ":" in ln:
            break
        title_lines.append(ln)
    out = {"baslik_pdf": " ".join(title_lines)}
    pats = {
        "kanun_numarasi": r"Kanun Numaras[ıi]\s*:\s*(\d+)",
        "kabul_tarihi": r"Kabul Tarihi\s*:\s*([\d/]+)",
        "rg_tarihi": r"R(?:esmî|\.)\s*Gazete\s*:\s*Tarih\s*:\s*([\d/]+)",
        "rg_sayisi": r"Sayı\s*:\s*(\d+)",
    }
    for k, p in pats.items():
        m = re.search(p, header_text)
        if m:
            out[k] = m.group(1)
    return out


def _latest_dated(items: list[tuple[str, str]]) -> dict | None:
    """[(metin, kaynak)] içinden en geç tarihli olanı döndürür."""
    best = None
    for text, src in items:
        for m in DATE_RE.finditer(text):
            iso = _iso(m.group(0))
            if best is None or iso > best["tarih"]:
                best = {"tarih": iso, "kaynak": src, "ifade": text[:200]}
    return best


def _mulga_info(text: str, tur: str) -> dict | None:
    m = ch.MULGA_RE.search(text)
    if not m:
        return None
    dayanak_raw = m.group("dayanak").strip()
    if m.group("rg"):
        dayanak = f"{m.group('tarih')} tarihli ve {dayanak_raw} sayılı Resmî Gazete'de yayımlanan değişiklik"
    else:
        km = re.match(r"(\d+)/(\d+)\s*md\.?", dayanak_raw)
        dayanak = f"{km.group(1)} sayılı Kanunun {km.group(2)}. maddesi" if km else dayanak_raw
    return {"tarih": _iso(m.group("tarih")), "dayanak": dayanak, "ham": m.group(0)}


# ---------------------------------------------------------------- ana akış

def build_document(spec: DocSpec) -> DocResult:
    pdf = DOCS_RAW / spec.dosya
    is_reg = spec.tur == "yonetmelik"
    ex = extract(pdf, is_regulation=is_reg)
    articles = ch.parse_articles(ex.paragraphs)
    known_fn = set(ex.footnotes)

    # ---- belge üstverisi
    hdr = _parse_header(spec, ex.header_text)
    belge_adi = tr_title(hdr["baslik_pdf"])
    if spec.tur == "kanun":
        tam_ad = f"{spec.numara} sayılı {belge_adi}"
    else:
        tam_ad = belge_adi
    app_text = "\n".join(ln.text for ln in ex.appendix_lines)

    amend_notes = []
    for p in ex.paragraphs:
        amend_notes += [(n, "metin içi değişiklik notu") for n in ch.find_amendments(p.text)]
    fn_items = [(v, f"dipnot {k}") for k, v in ex.footnotes.items()]
    rg_list = None
    if is_reg:
        rows = re.findall(r"^\s*\d+\.\s+(\d{1,2}/\d{1,2}/\d{4})\s+(\d+)", app_text, re.M)
        first = re.search(r"(\d{1,2}/\d{1,2}/\d{4})\s+(\d+)", app_text)
        if first:
            hdr["rg_tarihi"], hdr["rg_sayisi"] = first.group(1), first.group(2)
        if rows:
            rg_list = {"tarih": _iso(rows[-1][0]), "rg_sayisi": rows[-1][1],
                       "kaynak": "değiştiren yönetmelikler listesi (son satır)"}

    meta = {
        "belge_id": spec.belge_id,
        "dosya": spec.dosya,
        "tur": spec.tur,
        "numara": spec.numara,
        "kisa_ad": spec.kisa_ad,
        "belge_adi": belge_adi,
        "tam_ad": tam_ad,
        "kabul_tarihi": _iso(hdr["kabul_tarihi"]) if "kabul_tarihi" in hdr else None,
        "resmi_gazete": {"tarih": _iso(hdr["rg_tarihi"]) if "rg_tarihi" in hdr else None,
                         "sayi": hdr.get("rg_sayisi")},
        "kaynak": "mevzuat.gov.tr",
        "indirme_tarihi": spec.indirme_tarihi,
        "son_degisiklik": {
            "metin_ici_en_son_degisiklik_notu": _latest_dated(amend_notes),
            "dipnotlardaki_en_gec_tarih": _latest_dated(fn_items),
            "degistiren_yonetmelikler_listesi_son": rg_list,
            "pdf_olusturma_tarihi": _pdf_date(ex.pdf_metadata.get("creationDate", "")),
        },
    }

    # ---- madde parçaları
    chunks: list[dict] = []
    used_fn: set[str] = set()
    for a in articles:
        fn_loc = _footnote_locations(a, known_fn)
        intro_clean = FN_TOKEN_RE.sub("", a.intro).strip()
        mulga = None
        body_text = " ".join(p for f in a.fikralar for p in f.paras)
        if not FN_TOKEN_RE.sub("", body_text).strip() and "Mülga" in a.intro:
            mulga = _mulga_info(a.intro, spec.tur)
        base = {
            "belge_id": spec.belge_id, "belge_kisa_ad": spec.kisa_ad, "belge_adi": tam_ad,
            "belge_turu": spec.tur,
            "madde_no": a.madde_no, "madde_etiketi": a.madde_etiketi, "madde_basligi": a.baslik,
            "kisim": a.kisim, "bolum": a.bolum,
        }
        header_core = f"{tam_ad} ({spec.kisa_ad}) · {a.madde_etiketi}" + (f" · {a.baslik}" if a.baslik else "")

        if mulga:
            text = f"{a.madde_etiketi} – {a.intro}".strip()
            durum_cumlesi = (f"Bu madde yürürlükten kaldırılmıştır (mülga). Kaldırılma tarihi: {mulga['tarih']}. "
                             f"Dayanak: {mulga['dayanak']}.")
            chunks.append({
                **base, "chunk_id": f"{spec.kisa_ad}-{_slug(a.madde_no)}-1", "tur": "mulga",
                "durum": "mulga", "mulga": mulga,
                "fikralar": [], "bentler": None, "parca": 1, "parca_sayisi": 1,
                "degisiklik_notlari": [mulga["ham"]], "dipnotlar": _fns(fn_loc, set(fn_loc), ex.footnotes),
                "sayfalar": sorted(a.pages), "indekse_dahil": True,
                "baglam_basligi": header_core, "metin": FN_TOKEN_RE.sub("", text),
                "arama_metni": f"{header_core}\n{durum_cumlesi}",
            })
            used_fn |= set(fn_loc)
            continue

        pieces = ch.split_article(a, MAX_CHUNK_WORDS)
        for i, pc in enumerate(pieces, 1):
            raw = "\n".join(pc.text_parts)
            if i == 1 and a.intro:
                raw = a.intro + "\n" + raw
            markers = set()
            for tok in FN_TOKEN_RE.findall(raw + " " + a.intro):
                markers |= set(ch.segment_markers(tok, known_fn))
            for tok in a.baslik_fn:
                markers |= set(ch.segment_markers(tok, known_fn))
            used_fn |= markers
            metin = re.sub(r"[ \t]{2,}", " ", FN_TOKEN_RE.sub("", raw)).strip()
            fik = [f for f in pc.fikra_nos if f is not None]
            header = header_core
            if len(pieces) > 1:
                header += f" · {_fikra_label(fik)}" + (f" ({', '.join(pc.bentler)} bentleri)" if pc.bentler else "")
            chunks.append({
                **base,
                "chunk_id": f"{spec.kisa_ad}-{_slug(a.madde_no)}-{i}",
                "tur": "madde", "durum": "yururlukte", "mulga": None,
                "fikralar": fik, "bentler": pc.bentler,
                "parca": i, "parca_sayisi": len(pieces),
                "degisiklik_notlari": ch.find_amendments(metin),
                "dipnotlar": _fns(fn_loc, markers, ex.footnotes),
                "sayfalar": sorted(pc.pages),
                "indekse_dahil": True,
                "baglam_basligi": header,
                "metin": metin,
                "arama_metni": f"{header}\n{ch.strip_amendments(metin)}",
            })

    # ---- ekler: ceza tablosu ve (yönetmelikte) örnek cayma formu
    table = None
    if not is_reg and "TABLO" in app_text:
        intro = []
        for ln in ex.appendix_lines:
            if "maddesinin;" in ln.text:
                break
            intro.append(ln.text)
        table = tb.extract_penalty_table(pdf, ex.appendix_start_page, " ".join(intro))
        if table:
            madde = "77 nci" if spec.numara == "6502" else "12 nci"
            ttext = tb.table_to_text(table, spec.numara, madde)
            header = f"{tam_ad} ({spec.kisa_ad}) · {madde.split()[0]}. madde idari para cezaları tablosu ({table.yil})"
            chunks.append({
                "belge_id": spec.belge_id, "belge_kisa_ad": spec.kisa_ad, "belge_adi": tam_ad,
                "belge_turu": spec.tur,
                "madde_no": f"Tablo-{table.yil}", "madde_etiketi": f"Ek tablo ({table.yil})",
                "madde_basligi": table.baslik, "kisim": None, "bolum": None,
                "chunk_id": f"{spec.kisa_ad}-tablo{table.yil}-1", "tur": "tablo", "durum": "yururlukte",
                "mulga": None, "yil": table.yil, "ilgili_madde": madde.split()[0],
                "fikralar": [], "bentler": None, "parca": 1, "parca_sayisi": 1,
                "degisiklik_notlari": [], "dipnotlar": [],
                "sayfalar": table.sayfalar,
                # İnsan onayı gelene kadar indekse girmez (karar 2).
                "indekse_dahil": False,
                "baglam_basligi": header, "metin": ttext, "arama_metni": f"{header}\n{ttext}",
                "satirlar": [r.__dict__ for r in table.satirlar],
            })

    if is_reg:
        form_lines, on = [], False
        for ln in ex.appendix_lines:
            if ln.text.strip() == "EK":
                on = True
                continue
            if on:
                form_lines.append(ln.text)
        if form_lines:
            baslik = tr_title(form_lines[0])
            metin = "\n".join(form_lines[1:])
            header = f"{tam_ad} ({spec.kisa_ad}) · Ek · {baslik}"
            chunks.append({
                "belge_id": spec.belge_id, "belge_kisa_ad": spec.kisa_ad, "belge_adi": tam_ad,
                "belge_turu": spec.tur, "madde_no": "Ek", "madde_etiketi": "Ek",
                "madde_basligi": baslik, "kisim": None, "bolum": None,
                "chunk_id": f"{spec.kisa_ad}-ek-1", "tur": "ek", "durum": "yururlukte", "mulga": None,
                "fikralar": [], "bentler": None, "parca": 1, "parca_sayisi": 1,
                "degisiklik_notlari": [], "dipnotlar": [],
                "sayfalar": sorted({ln.page for ln in ex.appendix_lines if ln.text in form_lines}),
                "indekse_dahil": True, "baglam_basligi": header,
                "metin": metin, "arama_metni": f"{header}\n{metin}",
            })

    # ---- tanılama
    raw_headers = _independent_header_count(pdf, ex.appendix_start_page)
    diag = {
        "madde_sayisi": len(articles),
        "bagimsiz_baslik_sayimi": raw_headers,
        "dipnot_sayisi": len(ex.footnotes),
        "baglanmayan_dipnotlar": sorted(known_fn - used_fn, key=int),
        "basliksiz_maddeler": [a.madde_etiketi for a in articles if not a.baslik],
        "fikra_sira_atlamalari": [
            (a.madde_etiketi, [f.no for f in a.fikralar]) for a in articles
            if [f.no for f in a.fikralar if f.no is not None] !=
            list(range(1, 1 + len([f for f in a.fikralar if f.no is not None])))
        ],
        "ek_bolumu_baslangic_sayfasi": ex.appendix_start_page,
        "ek_bolumu_ilk_satirlar": [ln.text for ln in ex.appendix_lines[:3]],
        "dislanan_ekler": _excluded_appendix(app_text, is_reg),
    }
    return DocResult(meta=meta, chunks=chunks, diag=diag, table=table)


def _fikra_label(nos: list[int]) -> str:
    if not nos:
        return "giriş"
    if len(nos) == 1:
        return f"fıkra {nos[0]}"
    return f"fıkra {nos[0]}–{nos[-1]}"


def _footnote_locations(a: ch.Article, known: set[str]) -> dict[str, str]:
    loc: dict[str, str] = {}
    for tok in a.baslik_fn:
        for n in ch.segment_markers(tok, known):
            loc.setdefault(n, "madde başlığı")
    for tok in FN_TOKEN_RE.findall(a.intro):
        for n in ch.segment_markers(tok, known):
            loc.setdefault(n, "madde girişi")
    for f in a.fikralar:
        for p in f.paras:
            for tok in FN_TOKEN_RE.findall(p):
                for n in ch.segment_markers(tok, known):
                    loc.setdefault(n, f"fıkra {f.no}" if f.no else "madde metni")
    return loc


def _fns(loc: dict[str, str], wanted: set[str], footnotes: dict[str, str]) -> list[dict]:
    out = []
    for n in sorted(wanted, key=lambda x: int(x) if x.isdigit() else 0):
        if n not in footnotes:
            continue
        out.append({"no": n, "tur": ch.classify_footnote(footnotes[n]),
                    "konum": loc.get(n, "bilinmiyor"), "metin": footnotes[n]})
    return out


def _independent_header_count(pdf, appendix_page: int | None) -> int:
    """Paragraf mantığından bağımsız sayım: ham sayfa metninde satır başı 'MADDE n –' kalıbı.
    Ek bölümünün başladığı sayfada ek başlığından sonrası sayılmaz."""
    doc = pymupdf.open(pdf)
    n = 0
    for i, page in enumerate(doc):
        if appendix_page and i + 1 > appendix_page:
            break
        txt = page.get_text()
        if appendix_page and i + 1 == appendix_page:
            cut = re.search(r"^\s*(\d{4} SAYILI|\(I\) SAYILI|Yönetmeliğin Yayımlandığı)", txt, re.M)
            txt = txt[:cut.start()] if cut else txt
        n += len([m for m in re.finditer(r"^\s*(?:(?:GEÇİCİ|EK)\s+)?MADDE\s+\d+(?:/[A-Z])?\s*[-–−]", txt, re.M)])
    return n


def _excluded_appendix(app_text: str, is_reg: bool) -> list[str]:
    out = []
    if "YÜRÜRLÜĞE GİRİŞ TARİHİNİ GÖSTERİR LİSTE" in app_text:
        out.append("Değişiklik/yürürlük tarihleri listesi (tarihçe; madde metni değil)")
    if "CETVEL" in app_text:
        out.append("Kadro cetveli (teşkilat kadro listesi)")
    if is_reg and "Yayımlandığı Resmî Gazete" in app_text:
        out.append("Resmî Gazete yayım/değişiklik listesi (yalnızca belge üstverisine işlendi)")
    return out
