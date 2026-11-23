"""Komut satırından soru sorma: arama + cevap üretimi + doğrulama.

    python ask.py "İnternetten aldığım ürünü kaç gün içinde iade edebilirim?"
    python ask.py "..." --json          # tüm alanlar (çıkarılan cümleler, ham çıktı dahil)
    python ask.py "..." --model claude-sonnet-5-5
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from mevzuat_rag.answer import CEVAP_MODEL, Cevaplayici, cevap_sozlugu  # noqa: E402

DURUM_AD = {"cevaplandi": "cevaplandı", "kismen_cevaplandi": "kısmen cevaplandı",
            "bulunamadi": "bu belgelerde bulunamadı"}


def yazdir(c) -> None:
    if c.ust_not:                                    # doğrulama notu cevabın ÜSTÜNDE
        print(f"⚠ {c.ust_not}\n")
    print(f"Durum: {DURUM_AD.get(c.durum, c.durum)}\n")
    kaynak_no = {k["parca_id"]: i for i, k in enumerate(c.kaynaklar, 1)}
    for cm in c.cumleler:
        refs = "".join(f"[{kaynak_no[d['parca_id']]}]" for d in cm.dayanaklar if d["parca_id"] in kaynak_no)
        print(f"{cm.metin} {refs}")
    if c.durum == "bulunamadi" and not c.cumleler:
        print("Bu soru, kapsamdaki dört belgede (6502, 6563, 6698 sayılı Kanunlar ve Mesafeli "
              "Sözleşmeler Yönetmeliği) bulunamadı.")
    if c.bulunamayan:
        print("\nBelgelerde bulunamayan kısımlar:")
        for b in c.bulunamayan:
            print(f"  - {b}")
    if c.uyarilar:
        print("\nUyarılar:")
        for u in c.uyarilar:
            print(f"  - [{u['tur']}] {u['metin']}")
    if c.kaynaklar:
        print("\nKaynaklar:")
        for k in c.kaynaklar:
            print(f"  [{kaynak_no[k['parca_id']]}] {k['atif']}  ({k['parca_id']})")
        print("\nAlıntılar:")
        for cm in c.cumleler:
            for d in cm.dayanaklar:
                print(f"  [{kaynak_no[d['parca_id']]}] “{d['alinti']}”")
    print(f"\n{c.kapanis}")
    print(f"\n(model {c.model} · {c.sure_sn:.1f} sn · ${c.maliyet_usd:.5f} · "
          f"yeniden yazım: {c.arama['yeniden_yazim']})")


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Mevzuat üzerinde kaynak gösteren soru cevaplama")
    ap.add_argument("soru")
    ap.add_argument("--model", default=CEVAP_MODEL)
    ap.add_argument("--json", action="store_true", help="tüm alanları JSON olarak yazdır")
    args = ap.parse_args()
    c = Cevaplayici(model=args.model).cevapla(args.soru)
    if args.json:
        print(json.dumps(cevap_sozlugu(c), ensure_ascii=False, indent=1))
    else:
        yazdir(c)


if __name__ == "__main__":
    main()
