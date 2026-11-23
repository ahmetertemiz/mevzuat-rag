"""Arayüzün örnek sorularının cevaplarını bir kez üretip data/ornek_cevaplar.json'a yazar.

Ortak anahtar yokken ya da geçersizken arayüz örnek sorulara bu kaydı gösterir. Yerelde (.env'deki
anahtarla) çalıştırılır; arayüzle aynı hat kullanılır (arayuz.cevaplayici_kur).
Kullanım: python scripts/ornek_cevaplari_uret.py
"""
from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))


def main() -> None:
    import anthropic
    import ast

    from mevzuat_rag.answer import CEVAP_MODEL, cevap_sozlugu
    from mevzuat_rag.arayuz import SayacliIstemci, cevaplayici_kur, ornek_cevaplar_yolu
    from mevzuat_rag.retrieve import Retriever
    from mevzuat_rag.rewrite import REWRITE_MODEL, load_dotenv

    # Örnek soru listesi streamlit_app.py'den okunur (tek kaynak; Streamlit import edilmez).
    agac = ast.parse((ROOT / "streamlit_app.py").read_text(encoding="utf-8"))
    sorular = next(ast.literal_eval(n.value) for n in agac.body
                   if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "ORNEK_SORULAR")
    load_dotenv()
    r = Retriever(load_model=False)
    out = {"uretim_tarihi": dt.date.today().isoformat(), "model": CEVAP_MODEL,
           "yeniden_yazim_modeli": REWRITE_MODEL, "cevaplar": {}}
    for q in sorular:
        ist = SayacliIstemci(anthropic.Anthropic(timeout=60.0, max_retries=2), None)
        c = cevaplayici_kur(r, ist).cevapla(q)
        out["cevaplar"][q] = {"cevap": cevap_sozlugu(c), "cagri": ist.cagri_sayisi}
        print(f"{c.durum:18s} {len(c.cumleler)} cümle  {q}")
    ornek_cevaplar_yolu().write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print("->", ornek_cevaplar_yolu())


if __name__ == "__main__":
    main()
