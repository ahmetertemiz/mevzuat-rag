"""Değerlendirme ölçütünün mantığı (model gerektirmez)."""
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import eval_retrieval as ev  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def _hit(belge, madde, score=1.0):
    return SimpleNamespace(chunk={"belge_kisa_ad": belge, "madde_no": madde}, score=score)


def test_parcalar_maddeye_indirgenir_sira_korunur():
    hits = [_hit("TKHK", "48"), _hit("TKHK", "48"), _hit("MSY", "9"), _hit("TKHK", "48"), _hit("MSY", "5")]
    assert [a for a, _ in ev.ranked_articles(hits)] == ["TKHK:48", "MSY:9", "MSY:5"]


class FakeRetriever:
    chunks = [None] * 4

    def __init__(self, order):
        self.order = order

    def search(self, q, k, mode):
        return [_hit(*a.split(":")) for a in self.order]


def test_alternatif_ve_iki_gereksinim():
    qs = [
        {"id": "A", "tur": "madde_dili", "soru": "x", "dogru": [["MSY:9", "TKHK:48"]]},
        {"id": "B", "tur": "iki_madde", "soru": "y", "dogru": [["MSY:13"], ["MSY:12"]]},
    ]
    r = FakeRetriever(["TKHK:48", "MSY:13", "KVKK:1", "MSY:12"])
    res = ev.evaluate(r, qs)["dense"]
    assert res[0]["gereksinim_siralari"] == [1] and res[0]["tumu@1"]
    assert res[1]["gereksinim_siralari"] == [2, 4]
    assert res[1]["biri@3"] and not res[1]["tumu@3"] and res[1]["tumu@5"]


def test_soru_seti_bicimi():
    for name in ("retrieval.yaml", "holdout.yaml"):
        data = yaml.safe_load((ROOT / "evals" / name).read_text(encoding="utf-8"))
        assert "sorular" in data
    qs = yaml.safe_load((ROOT / "evals" / "retrieval.yaml").read_text(encoding="utf-8"))["sorular"]
    assert len(qs) == 30
    assert sum(q["tur"] == "madde_numarasi" for q in qs) == 5
    assert sum(q["tur"] == "cevapsiz" for q in qs) == 4
    assert all(q["dogru"] == [] for q in qs if q["tur"] == "cevapsiz")
    assert all(len(q["dogru"]) == 2 for q in qs if q["tur"] == "iki_madde")


def test_varsayilan_hat_cok_kosu_ozeti(tmp_path):
    """--varsayilan --runs N: her koşu ayrı ölçülür; en düşük / medyan / en yüksek raporlanır.
    Sahte yazıcı koşudan koşuya farklı sorgu üretir (model çağrısı yok)."""
    from mevzuat_rag.pipeline import Arayici
    from mevzuat_rag.retrieve import Retriever
    from mevzuat_rag.rewrite import Rewrite

    class Degisken:
        def __init__(self):
            self.i = 0

        def rewrite(self, q):
            self.i += 1
            # 1. koşu: yardımcı sorgu; 2. koşu: alakasız sorgu; 3. koşu: hata (düz BM25'e düşer)
            kosu = (self.i - 1) // 2 + 1
            if kosu == 3:
                raise RuntimeError("API hatası")
            sg = ["mesafeli sözleşmelerde cayma hakkı"] if kosu == 1 else ["xyzqw"]
            return Rewrite(q, sg, "sahte", 1, 1, 0.0, 0.1, "end_turn", [])

    qs = [
        {"id": "A", "tur": "gunluk_dil", "soru": "ayakkabıyı beğenmedim geri verebilir miyim",
         "dogru": [["MSY:9", "TKHK:48"]]},
        {"id": "B", "tur": "madde_numarasi", "soru": "6502 m.48", "dogru": [["TKHK:48"]]},
    ]
    a = Arayici(retriever=Retriever(load_model=False), rewriter=Degisken())
    ozet = ev.evaluate_default(qs, "test", runs=3, arayici=a, out_dir=tmp_path)
    assert all(len(v) == 3 for v in ozet.values())
    rapor = (tmp_path / "RAPOR_test_varsayilan.md").read_text(encoding="utf-8")
    assert "en düşük / medyan / en yüksek" in rapor and "**3 koşu**" in rapor
    data = json.loads((tmp_path / "sonuclar_test_varsayilan.json").read_text(encoding="utf-8"))
    assert len(data["kosular"]) == 3
    assert [r["yeniden_yazim"] for r in data["kosular"][2]] == ["başarısız", "başarısız"]


def test_ozet_bicimi():
    assert ev._ozet([12, 14, 13]) == "12 / 13 / 14"
    assert ev._ozet([21, 21]) == "21 / 21 / 21"


def test_cevap_olcutleri():
    sys.path.insert(0, str(ROOT / "scripts"))
    import eval_answers as ea
    chunks = {"MSY-m9-1": {"belge_kisa_ad": "MSY", "madde_no": "9"},
              "TKHK-m11-1": {"belge_kisa_ad": "TKHK", "madde_no": "11"}}
    q = {"id": "X", "tur": "normal", "dayanak": [["MSY:9", "TKHK:48"]], "olgular": [["on dört gün", "14 gün"], ["yok"]]}
    c = {"durum": "cevaplandi", "baglam_parcalari": ["MSY-m9-1", "TKHK-m11-1"],
         "cumleler": [{"metin": "Süre 14 gündür.", "dayanaklar": [{"parca_id": "MSY-m9-1", "dogrulandi": True}]}],
         "cikarilan_cumleler": [{"metin": "x", "dayanaklar": [{"parca_id": "TKHK-m11-1", "dogrulandi": False}]}],
         "uyarilar": [], "maliyet_usd": 0.002, "sure_sn": 3.0, "arama": {"maliyet_usd": 0.0005}}
    r = ea.olc(q, c, chunks)
    assert r["madde_dogru"] and r["baglamda"] and not r["yanlis_ret"]
    assert (r["olgu_bulunan"], r["olgu_toplam"]) == (1, 2)
    assert (r["alinti_dogru"], r["alinti_toplam"]) == (1, 2)
    assert (r["cumle_cikarilan"], r["cumle_toplam"]) == (1, 2)
    assert r["maliyet"] == pytest.approx(0.0015)
    qc = {"id": "Y", "tur": "cevapsiz", "dayanak": [], "olgular": []}
    rc = ea.olc(qc, {**c, "durum": "bulunamadi", "cumleler": [], "cikarilan_cumleler": []}, chunks)
    assert rc["dogru_ret"] and not rc["yanlis_ret"]
