"""Değerlendirme ölçütünün mantığı (model gerektirmez)."""
import sys
from pathlib import Path
from types import SimpleNamespace

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
