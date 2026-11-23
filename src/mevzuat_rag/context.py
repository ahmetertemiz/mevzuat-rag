"""Cevap üretimi için bağlam kurma (model çağrısı yapmaz).

Modele giden metin üç bloktan oluşur:
  <belgeler>  her belge bir kez: tam ad, kısaltma, indirme tarihi, PDF metin tarihi, metindeki son
              değişiklik notu tarihi
  <parcalar>  arama sırasıyla ilk k parça (+ ceza tablosu için bağlı madde parçaları); her parça
              kimliğiyle, bağlam başlığıyla, durumuyla (yürürlükte / MÜLGA) ve resmî metniyle
  <dipnotlar> (belge, no) ile tekilleştirilmiş dipnotlar; parçalar bunlara kimlikle atıf yapar

Modele verilmeyenler: yeniden yazılmış sorgular (bilgi sızdırabilir), arama_metni.
Ceza tablosu tek başına kullanılmaz (docs/cevap_uretimi_notlari.md §1): tablo bağlamdaysa,
bağlı olduğu madde parçalarından BM25 skoru en yüksek MAX_TABLO_EK tanesi de eklenir.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

import numpy as np

from . import config

K_VARSAYILAN = 8
MAX_TABLO_EK = 3
ATIF_TAKIBI_VARSAYILAN = False   # atıf takibi kabul kuralına göre (docs/kararlar.md)


@dataclass
class Baglam:
    parcalar: list[dict]                      # modele gösterilen parçalar (sırayla)
    ek_parcalar: list[str]                    # tablo bağlantısıyla eklenen parça kimlikleri
    dipnotlar: dict[str, dict]                # "TKHK-dn14" -> dipnot
    belgeler: dict[str, dict]                 # belge_id -> belge üstverisi
    metin: str                                # modele giden bağlam metni
    by_id: dict[str, dict] = field(default_factory=dict)


def belge_kaydi() -> dict[str, dict]:
    docs = json.loads(config.DOCS_META_PATH.read_text(encoding="utf-8"))
    return {d["belge_id"]: d for d in docs}


def dipnot_id(parca: dict, no: str) -> str:
    return f"{parca['belge_kisa_ad']}-dn{no}"


def _atif_yapilan_tablolar(parcalar: list[dict], retriever) -> list[dict]:
    """Bağlamdaki bir parçanın dipnotu ceza tablosuna atıf yapıyorsa ('tablo_atfi'), aynı belgenin
    tablo parçası. Ör. TKHK m.77 parçaları 'tutarlar için metin sonundaki tabloya bakınız' der;
    tablo bağlamda yoksa model eski (metindeki) tutarı güncel sanabilir (A03 hatası)."""
    var = {p["chunk_id"] for p in parcalar}
    belgeler = [p["belge_id"] for p in parcalar
                if any(d.get("tur") == "tablo_atfi" for d in p.get("dipnotlar") or [])]
    out = []
    for bid in dict.fromkeys(belgeler):
        for c in retriever.chunks:
            if c["belge_id"] == bid and c.get("tur") == "tablo" and c["chunk_id"] not in var:
                out.append(c)
                var.add(c["chunk_id"])
    return out


def tablo_atfi_var(p: dict) -> bool:
    return any(d.get("tur") == "tablo_atfi" for d in p.get("dipnotlar") or [])


def _tablo_ekleri(parcalar: list[dict], soru: str, retriever) -> list[dict]:
    """Bağlamdaki tablo parçalarının bağlı madde parçalarından, soruya BM25 skoru en yüksek olanlar."""
    var = {p["chunk_id"] for p in parcalar}
    idx = {c["chunk_id"]: i for i, c in enumerate(retriever.chunks)}
    adaylar = []
    for p in parcalar:
        if p.get("tur") == "tablo":
            adaylar += [cid for cid in p.get("ilgili_parcalar") or [] if cid not in var and cid in idx]
    if not adaylar:
        return []
    skor = retriever.bm25_scores(soru)
    adaylar = list(dict.fromkeys(adaylar))
    adaylar.sort(key=lambda cid: -float(skor[idx[cid]]) if isinstance(skor, np.ndarray) else 0)
    return [retriever.chunks[idx[cid]] for cid in adaylar[:MAX_TABLO_EK]]


# ------------------------------------------------------------------ atıf takibi (docs/kararlar.md)

ATIF_ILK_N = 3        # yalnız aramanın ilk bu kadar parçasındaki atıflar izlenir
MAX_ATIF_EK = 3       # en fazla bu kadar parça eklenir; tek adım (eklenenin atıfları izlenmez)

_ORD = r"(?:inci|ıncı|uncu|üncü|nci|ncı|ncu|ncü|ci|cı|cu|cü)"
_NO = r"\d+(?:/[A-ZÇĞİÖŞÜ])?"
_SIRA_SOZ = {"birinci": 1, "ikinci": 2, "üçüncü": 3, "dördüncü": 4, "beşinci": 5, "altıncı": 6,
             "yedinci": 7, "sekizinci": 8, "dokuzuncu": 9, "onuncu": 10, "on birinci": 11,
             "on ikinci": 12, "on üçüncü": 13, "on dördüncü": 14, "on beşinci": 15, "on altıncı": 16,
             "on yedinci": 17, "on sekizinci": 18, "on dokuzuncu": 19, "yirminci": 20}
_ATIF = re.compile(
    rf"((?:{_NO}(?:\s*['’]?\s*{_ORD})?\s*(?:,|\bve\b|\bile\b|\bveya\b)\s*)*{_NO}(?:\s*['’]?\s*{_ORD})?)"
    rf"\s+madde\w*"
    rf"(?:\s+({'|'.join(sorted(_SIRA_SOZ, key=len, reverse=True))})\s+fıkra)?")
_BELGE_ADI = re.compile(r"(?:\b[Bb]u\s+)?(?:Kanun|Yönetmeli[kğ]|Kararname|Tüzü[kğ])\w*")


def madde_atiflari(metin: str) -> list[tuple[str, int | None]]:
    """Metindeki aynı belgeye yapılan madde atıfları: [(madde_no, fıkra|None)], metin sırasıyla.
    Cümlede atıftan önce geçen son belge adı "bu Kanun/Yönetmelik" değilse (ör. "213 sayılı Kanunun",
    "Türk Borçlar Kanununun") atıf dış atıf sayılır ve alınmaz."""
    out: list[tuple[str, int | None]] = []
    for m in _ATIF.finditer(metin):
        bas = max(metin.rfind(ch, 0, m.start()) for ch in ".;\n")
        pencere = metin[bas + 1:m.start()]
        adlar = _BELGE_ADI.findall(pencere)
        if adlar and not re.match(r"[Bb]u\s", adlar[-1]):
            continue
        nolar = re.findall(_NO, m.group(1))
        fikra = _SIRA_SOZ.get(m.group(2)) if m.group(2) else None
        for i, no in enumerate(nolar):
            out.append((no, fikra if i == len(nolar) - 1 else None))
    return out


def _atif_ekleri(ilk: list[dict], mevcut: list[dict], soru: str, retriever) -> list[tuple[dict, dict]]:
    """İlk ATIF_ILK_N parçanın aynı belgeye madde atıflarından atıf yapılan parçalar (en fazla
    MAX_ATIF_EK, soruya BM25 skoruna göre). Dönüş: [(eklenen parça, atıf yapan parça)]."""
    var = {p["chunk_id"] for p in mevcut}
    idx = {c["chunk_id"]: i for i, c in enumerate(retriever.chunks)}
    adaylar: list[tuple[dict, dict]] = []
    for p in ilk[:ATIF_ILK_N]:
        if p.get("tur") == "tablo":
            continue
        for no, fikra in madde_atiflari(p.get("metin") or ""):
            if no == p.get("madde_no"):
                continue
            parcalar = sorted((c for c in retriever.chunks if c["belge_id"] == p["belge_id"]
                               and c.get("madde_no") == no and c.get("tur") != "tablo"),
                              key=lambda c: c.get("parca") or 0)
            if not parcalar:
                continue
            hedef = next((c for c in parcalar if fikra and fikra in (c.get("fikralar") or [])), parcalar[0])
            if hedef["chunk_id"] in var or any(hedef is a for a, _ in adaylar):
                continue
            adaylar.append((hedef, p))
    if len(adaylar) > MAX_ATIF_EK:
        skor = retriever.bm25_scores(soru)
        sira = {id(a): i for i, (a, _) in enumerate(adaylar)}
        adaylar.sort(key=lambda ap: (-float(skor[idx[ap[0]["chunk_id"]]]), sira[id(ap[0])]))
    return adaylar[:MAX_ATIF_EK]


def _durum(p: dict) -> str:
    if p.get("tur") == "mulga" or p.get("durum") == "mulga":
        m = p.get("mulga") or {}
        return f"MÜLGA (yürürlükten kaldırıldı) — kaldırılma tarihi {m.get('tarih')}, dayanak: {m.get('dayanak')}"
    if p.get("tur") == "tablo":
        return (f"idari para cezası tablosu ({p.get('yil')} yılı tutarları); bağlı madde: "
                f"{p.get('ilgili_madde')}. madde")
    return "yürürlükte"


def kur(hits_or_chunks, soru: str, retriever=None, k: int = K_VARSAYILAN,
        belgeler: dict[str, dict] | None = None, atif_takibi: bool | None = None) -> Baglam:
    """hits_or_chunks: arama sonucu (Hit listesi) ya da parça sözlükleri, en iyiden kötüye."""
    parcalar = [getattr(h, "chunk", h) for h in hits_or_chunks][:k]
    tablo_ekleri = _atif_yapilan_tablolar(parcalar, retriever) if retriever is not None else []
    madde_ekleri = (_tablo_ekleri(parcalar + tablo_ekleri, soru, retriever)
                    if retriever is not None else [])
    atif_takibi = ATIF_TAKIBI_VARSAYILAN if atif_takibi is None else atif_takibi
    atif = (_atif_ekleri(parcalar, parcalar + tablo_ekleri + madde_ekleri, soru, retriever)
            if (atif_takibi and retriever is not None) else [])
    atif_ekleri = [a for a, _ in atif]
    atif_kaynak = {a["chunk_id"]: kaynak["chunk_id"] for a, kaynak in atif}
    ekler = tablo_ekleri + madde_ekleri + atif_ekleri
    tum = parcalar + ekler
    belgeler = belgeler if belgeler is not None else belge_kaydi()

    dipnotlar: dict[str, dict] = {}
    for p in tum:
        for d in p.get("dipnotlar") or []:
            did = dipnot_id(p, d["no"])
            if did not in dipnotlar:
                dipnotlar[did] = {**d, "id": did, "belge_id": p["belge_id"],
                                  "konum_madde": p.get("madde_etiketi")}

    # --- metin
    L = ["<belgeler>"]
    for bid in dict.fromkeys(p["belge_id"] for p in tum):
        b = belgeler.get(bid, {})
        s = b.get("son_degisiklik") or {}
        son = (s.get("metin_ici_en_son_degisiklik_notu") or {}).get("tarih")
        L.append(f"- {b.get('kisa_ad')}: {b.get('tam_ad')} | mevzuat.gov.tr'den indirildi: "
                 f"{b.get('indirme_tarihi')} | PDF metin tarihi: {s.get('pdf_olusturma_tarihi')} | "
                 f"metindeki en son değişiklik notu: {son}")
    L.append("</belgeler>\n\n<parcalar>")
    tablo_ids = {p["chunk_id"] for p in tablo_ekleri}
    madde_ids = {p["chunk_id"] for p in madde_ekleri}
    for p in tum:
        L.append(f"[{p['chunk_id']}] {p['baglam_basligi']}")
        if p["chunk_id"] in tablo_ids:
            L.append("(Aramada çıkmadı; bağlamdaki bir maddenin dipnotu bu tabloya atıf yaptığı için "
                     "eklendi. Tutarlar her yıl güncellenir; güncel tutar bu tablodadır.)")
        if p["chunk_id"] in madde_ids:
            L.append("(Aramada çıkmadı; ceza tablosunun bağlı olduğu madde parçası olarak eklendi.)")
        if p["chunk_id"] in atif_kaynak:
            L.append(f"(Aramada çıkmadı; bağlamdaki {atif_kaynak[p['chunk_id']]} parçası numarayla bu "
                     "maddeye atıf yaptığı için eklendi.)")
        L.append(f"Durum: {_durum(p)}")
        dn = [dipnot_id(p, d["no"]) for d in p.get("dipnotlar") or []]
        if dn:
            L.append("Dipnot atıfları: " + ", ".join(dn))
        L.append("Metin:\n" + p["metin"].strip())
        L.append("")
    L.append("</parcalar>")
    if dipnotlar:
        L.append("\n<dipnotlar>")
        for did, d in dipnotlar.items():
            L.append(f"[{did}] ({d['tur']}; {d['konum_madde']}, {d['konum']}) {d['metin']}")
        L.append("</dipnotlar>")
    return Baglam(tum, [p["chunk_id"] for p in ekler], dipnotlar,
                  {bid: belgeler.get(bid, {}) for bid in {p["belge_id"] for p in tum}},
                  "\n".join(L), {p["chunk_id"]: p for p in tum})
