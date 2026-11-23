"""PDF'leri işler; data/chunks.jsonl, data/belgeler.json ve reports/dogrulama.md üretir.

Kullanım:  python scripts/build_chunks.py
"""
from __future__ import annotations

import json
import random
import re
import statistics
import sys
from collections import Counter
from pathlib import Path

import pymupdf

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mevzuat_rag import config  # noqa: E402
from mevzuat_rag.build import build_document  # noqa: E402

SEED = 2026
IMG_DIR = config.REPORTS_DIR / "img"


def suspicious(c: dict) -> list[str]:
    """Bir parçada gözle bakılması gereken durumlar."""
    why = []
    m = c["metin"]
    n = len(m.split())
    if not m.strip():
        why.append("boş metin")
    if "⟨fn" in m or "⟨fn" in c["arama_metni"]:
        why.append("çözülmemiş dipnot işareti")
    if re.search(r"\b(?:GEÇİCİ |EK )?MADDE \d+\s*[-–−]", m) and c["tur"] != "mulga":
        why.append("metin içinde ikinci bir MADDE başlığı")
    if re.search(r"ibaresi .{0,120}(şeklinde değiştirilmiştir|eklenmiştir|çıkarılmıştır)", m):
        why.append("dipnot gibi görünen cümle gövdede")
    if re.search(r"[a-zçğıöşü][.,;:]\d{1,2}(?=\s|$)", m):
        why.append("kelimeye yapışık rakam (kaçmış dipnot işareti?)")
    if "\ufffd" in m:
        why.append("bozuk karakter")
    # bent etiketleri "a)", "1)" yalnız kapanış parantezi taşır; dengeyi onları çıkarıp ölç
    pm = re.sub(r"(?m)^\s*[a-zçğıöşü0-9]{1,2}\)", "", m)
    pm = re.sub(r"[a-zçğıöşü]\)\s", " ", pm)
    if pm.count("(") != pm.count(")"):
        why.append(f"parantez dengesiz ({pm.count('(')}/{pm.count(')')})")
    if c["tur"] == "madde" and c["parca"] == 1 and m[:1].islower():
        why.append("küçük harfle başlıyor")
    if c["tur"] == "madde" and n > config.MAX_CHUNK_WORDS * 1.3:
        why.append(f"sınırın çok üstünde ({n} kelime)")
    return why


def render_table_pages(doc_spec, pages: list[int]) -> list[str]:
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(config.DOCS_RAW / doc_spec.dosya)
    out = []
    for p in pages:
        name = f"{doc_spec.kisa_ad}_tablo_s{p}.png"
        doc[p - 1].get_pixmap(dpi=100).save(IMG_DIR / name)
        out.append(f"img/{name}")
    return out


def md_escape(s: str) -> str:
    return s.replace("|", "\\|").replace("\n", " ")


def main() -> None:
    config.DATA_DIR.mkdir(exist_ok=True)
    config.REPORTS_DIR.mkdir(exist_ok=True)
    results = {d.kisa_ad: (d, build_document(d)) for d in config.DOCS}

    all_chunks = [c for _, r in results.values() for c in r.chunks]
    ids = Counter(c["chunk_id"] for c in all_chunks)
    dup = [k for k, v in ids.items() if v > 1]
    assert not dup, f"yinelenen chunk_id: {dup}"

    with config.CHUNKS_PATH.open("w", encoding="utf-8", newline="\n") as f:
        for c in all_chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    config.DOCS_META_PATH.write_text(
        json.dumps([r.meta for _, r in results.values()], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8", newline="\n")

    L: list[str] = []
    w = L.append
    w("# Belge işleme doğrulama raporu\n")
    w("`python scripts/build_chunks.py` tarafından üretilir. Elle düzenlemeyin.\n")
    w(f"Toplam parça: **{len(all_chunks)}** "
      f"(indekse girecek: {sum(c['indekse_dahil'] for c in all_chunks)}, "
      f"indeks dışı: {sum(not c['indekse_dahil'] for c in all_chunks)})\n")

    # 1. özet
    w("## 1. Belge başına özet\n")
    w("| Belge | Madde (ayrıştırılan / bağımsız sayım) | Parça | Bölünen madde | Mülga madde | Dipnot (bağlanan / toplam) | Tablo | Ek |")
    w("|---|---|---|---|---|---|---|---|")
    for k, (d, r) in results.items():
        cs = r.chunks
        split = len({c["madde_no"] for c in cs if c["tur"] == "madde" and c["parca_sayisi"] > 1})
        fn_total = r.diag["dipnot_sayisi"]
        fn_bound = fn_total - len(r.diag["baglanmayan_dipnotlar"])
        ok = "✅" if r.diag["madde_sayisi"] == r.diag["bagimsiz_baslik_sayimi"] else "❌"
        w(f"| {k} ({d.numara}) | {r.diag['madde_sayisi']} / {r.diag['bagimsiz_baslik_sayimi']} {ok} | {len(cs)} | {split} "
          f"| {sum(c['tur'] == 'mulga' for c in cs)} | {fn_bound} / {fn_total} "
          f"| {sum(c['tur'] == 'tablo' for c in cs)} | {sum(c['tur'] == 'ek' for c in cs)} |")
    w("\n*Bağımsız sayım:* paragraf mantığı kullanılmadan, ham sayfa metninde satır başındaki "
      "`MADDE n –` kalıbı sayıldı.\n")

    # 2. üstveri
    w("## 2. Belge üstverisi\n")
    w("| Belge | Tam ad | Kabul | RG tarih / sayı | İndirme | PDF oluşturma | En son metin içi değişiklik notu | Dipnotlarda geçen en geç tarih |")
    w("|---|---|---|---|---|---|---|---|")
    for k, (d, r) in results.items():
        m = r.meta
        s = m["son_degisiklik"]
        mi = s["metin_ici_en_son_degisiklik_notu"]
        dn = s["dipnotlardaki_en_gec_tarih"]
        w(f"| {k} | {m['tam_ad']} | {m['kabul_tarihi'] or '—'} | {m['resmi_gazete']['tarih']} / {m['resmi_gazete']['sayi']} "
          f"| {m['indirme_tarihi']} | {s['pdf_olusturma_tarihi']} | {mi['tarih']} `{md_escape(mi['ifade'])}` "
          f"| {dn['tarih']} ({dn['kaynak']}) |")
    msy = results["MSY"][1].meta["son_degisiklik"]["degistiren_yonetmelikler_listesi_son"]
    if msy:
        w(f"\nMSY değiştiren yönetmelikler listesinin son satırı: {msy['tarih']}, RG sayı {msy['rg_sayisi']}.\n")
    w("*Not:* \"Dipnotlarda geçen en geç tarih\" ileri bir tarih olabilir (ör. AYM iptal kararının "
      "yürürlüğe gireceği gün). Bu bir değişiklik tarihi değil, belgede geçen en geç tarihtir.\n")

    # 3. uzunluklar
    w("## 3. Parça uzunlukları (kelime, `metin` alanı)\n")
    w("| Belge | En kısa | Medyan | En uzun |")
    w("|---|---|---|---|")
    for k, (_, r) in results.items():
        cs = [c for c in r.chunks if c["tur"] != "tablo"]
        ws = sorted((len(c["metin"].split()), c["chunk_id"]) for c in cs)
        w(f"| {k} | {ws[0][0]} (`{ws[0][1]}`) | {int(statistics.median(x for x, _ in ws))} | {ws[-1][0]} (`{ws[-1][1]}`) |")
    ws = sorted((len(c["metin"].split()), c["chunk_id"]) for c in all_chunks if c["tur"] != "tablo")
    w("\nTüm belgelerde en kısa 5: " + ", ".join(f"`{i}` ({n})" for n, i in ws[:5]))
    w("\nTüm belgelerde en uzun 5: " + ", ".join(f"`{i}` ({n})" for n, i in ws[-5:]))
    w(f"\nParça sınırı {config.MAX_CHUNK_WORDS} kelime. Bölünen parçalara bağlam için fıkranın giriş "
      "cümlesi eklendiğinden sınır biraz aşılabilir.\n")

    # 4. şüpheli
    w("## 4. Boş ya da şüpheli parçalar\n")
    sus = [(c["chunk_id"], why) for c in all_chunks for why in [suspicious(c)] if why]
    if not sus:
        w("Yok.\n")
    else:
        w("| Parça | Neden |")
        w("|---|---|")
        for cid, why in sus:
            w(f"| `{cid}` | {'; '.join(why)} |")
        w("")

    # 5. bilgi notları
    w("## 5. Yapısal bilgi notları\n")
    short = sorted((len(c["metin"].split()), c["chunk_id"]) for c in all_chunks
                   if c["tur"] in ("madde", "mulga") and len(c["metin"].split()) < 15)
    w("- **15 kelimeden kısa parçalar** (hata değil; yürürlük/yürütme gibi tek cümlelik maddeler): "
      + ", ".join(f"`{i}` ({n})" for n, i in short))
    w("- Aşağıdaki başlıksız maddeler ve fıkra atlamaları PDF'le karşılaştırıldı: geçici maddelerin "
      "PDF'te de başlığı yok; KVKK m.30'da fıkralar PDF'te \"(2) ila (5) - (… ile ilgili olup yerine "
      "işlenmiştir.)\" biçiminde tek satırda.")
    for k, (_, r) in results.items():
        dg = r.diag
        if dg["basliksiz_maddeler"]:
            w(f"- **{k}** başlıksız maddeler: {', '.join(dg['basliksiz_maddeler'])}")
        if dg["fikra_sira_atlamalari"]:
            w(f"- **{k}** fıkra numarası atlayan maddeler: "
              + ", ".join(f"{a} {n}" for a, n in dg["fikra_sira_atlamalari"]))
        if dg["baglanmayan_dipnotlar"]:
            w(f"- **{k}** hiçbir maddeye bağlanamayan dipnotlar: {dg['baglanmayan_dipnotlar']}")
    w("")

    # 6. dışlananlar
    w("## 6. İndekse alınmayan ek bölümler\n")
    for k, (_, r) in results.items():
        for x in r.diag["dislanan_ekler"]:
            w(f"- **{k}**: {x}")
    w("")

    # 7. tablolar
    w("## 7. İdari para cezası tabloları\n")
    w("Rakamlar sayfa görüntüleriyle karşılaştırıldı. Bir tablo yalnızca kullanıcı onayından sonra "
      "indekse girer (`build.py` içindeki `APPROVED_TABLES`). Her satır, karşılık geldiği madde "
      "parçasına `ilgili_parca` alanıyla bağlıdır.\n")
    for k, (d, r) in results.items():
        t = r.table
        if t is None:
            continue
        tc = next(c for c in r.chunks if c["tur"] == "tablo")
        links = [row["ilgili_parca"] for row in tc["satirlar"]]
        imgs = render_table_pages(d, t.sayfalar)
        same = Counter(t.hucre_sayilari) == Counter(t.ham_sayilar)
        w(f"### {k}: {t.baslik}\n")
        w(f"- Yıl: **{t.yil}** · PDF sayfaları: {', '.join(map(str, t.sayfalar))}")
        w(f"- Açıklama: {t.aciklama}")
        w(f"- Otomatik kontrol: hücrelerden okunan {len(t.hucre_sayilari)} sayı ile tutar sütunundaki "
          f"ham kelimelerden okunan {len(t.ham_sayilar)} sayı {'**aynı** ✅' if same else '**FARKLI** ❌'}")
        w(f"- Durum: {'**indekste** (onaylandı)' if tc['indekse_dahil'] else '**indeks dışı** (onay bekliyor)'}")
        w(f"- İlgili parçalar: {', '.join(f'`{x}`' for x in tc['ilgili_parcalar'])}")
        w("- Sayfa görüntüleri: " + ", ".join(f"[{Path(i).name}]({i})" for i in imgs) + "\n")
        w("| # | Bölüm | Fıkra | Bent | Alt bent | Tutar (TL) | Sayfa | İlgili parça |")
        w("|---|---|---|---|---|---|---|---|")
        for i, (row, link) in enumerate(zip(t.satirlar, links), 1):
            bolum = "güncel" if row.bolum == "guncel" else "Geçici m.3 (değişiklik öncesi 77. madde)"
            w(f"| {i} | {bolum} | {md_escape(row.fikra or '')} | {row.bent or ''} | {row.alt_bent or ''} "
              f"| {row.tutar} | {row.sayfa} | `{link}` |")
        w("")
    w("**Bilinen sınır (6502 tablosu):** Bazı satırlarda aynı fıkra/bent için birden çok tutar var "
      "(ör. dördüncü fıkra (a) bendi: 31.902.048 ve 22.329). Tablo hangi tutarın hangi duruma ait "
      "olduğunu söylemiyor; bu bilgi 77. maddenin metninde. Tutarlar tabloda göründüğü sırayla tutuluyor.\n")

    # 8. örnekler
    w(f"## 8. Rastgele örnekler (belge başına 3, seed={SEED})\n")
    rng = random.Random(SEED)
    for k, (_, r) in results.items():
        pool = [c for c in r.chunks if c["tur"] != "tablo"]
        for c in rng.sample(pool, 3):
            w(f"### `{c['chunk_id']}`\n")
            w(f"- **Bağlam başlığı:** {c['baglam_basligi']}")
            w(f"- **Madde:** {c['madde_etiketi']} · **Başlık:** {c['madde_basligi']} · "
              f"**Fıkralar:** {c['fikralar']} · **Bentler:** {c['bentler']} · "
              f"**Parça:** {c['parca']}/{c['parca_sayisi']} · **Sayfa:** {c['sayfalar']}")
            w(f"- **Kısım/Bölüm:** {c['kisim'] or '—'} / {c['bolum'] or '—'}")
            w(f"- **Değişiklik notları:** {c['degisiklik_notlari'] or '—'}")
            if c["dipnotlar"]:
                for dn in c["dipnotlar"]:
                    w(f"- **Dipnot {dn['no']}** ({dn['tur']}, {dn['konum']}): {dn['metin'][:300]}"
                      + ("…" if len(dn["metin"]) > 300 else ""))
            w("\n```text\n" + c["metin"] + "\n```\n")

    out = config.REPORTS_DIR / "dogrulama.md"
    out.write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
    print(f"{len(all_chunks)} parça -> {config.CHUNKS_PATH.relative_to(config.ROOT)}")
    print(f"rapor -> {out.relative_to(config.ROOT)}")
    print(f"şüpheli parça: {len(sus)}")


if __name__ == "__main__":
    main()
