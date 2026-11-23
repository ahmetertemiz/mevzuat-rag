"""Proje genelindeki sabitler: yollar ve belge kaydı.

Belge kaydı elle tutulur, çünkü kısa ad (TKHK, ETK...) ve indirme tarihi PDF'te yazmaz.
Başlık, numara ve Resmî Gazete bilgileri PDF'ten okunur ve bu kayıtla karşılaştırılır.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCS_RAW = ROOT / "docs_raw"
DATA_DIR = ROOT / "data"
CHUNKS_PATH = DATA_DIR / "chunks.jsonl"
DOCS_META_PATH = DATA_DIR / "belgeler.json"
REPORTS_DIR = ROOT / "reports"
INDEX_DIR = ROOT / "index"

# Bir parçanın gövdesi için üst sınır (kelime). Bunu aşan maddeler fıkra/bent sınırından bölünür.
MAX_CHUNK_WORDS = 350


@dataclass(frozen=True)
class DocSpec:
    belge_id: str      # dosya adının kökü, ör. "1.5.6502"
    dosya: str
    tur: str           # "kanun" | "yonetmelik"
    numara: str        # kanun numarası; yönetmelikte mevzuat.gov.tr numarası
    kisa_ad: str
    indirme_tarihi: str


INDIRME_TARIHI = "2026-11-23"

DOCS: list[DocSpec] = [
    DocSpec("1.5.6502", "1.5.6502.pdf", "kanun", "6502", "TKHK", INDIRME_TARIHI),
    DocSpec("1.5.6563", "1.5.6563.pdf", "kanun", "6563", "ETK", INDIRME_TARIHI),
    DocSpec("1.5.6698", "1.5.6698.pdf", "kanun", "6698", "KVKK", INDIRME_TARIHI),
    DocSpec("7.5.20237", "7.5.20237.pdf", "yonetmelik", "20237", "MSY", INDIRME_TARIHI),
]
