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
class EmbedSpec:
    key: str              # index/<key>/ klasör adı ve komut satırı adı
    name: str             # Hugging Face model adı
    max_tokens: int       # en uzun parçayı kesmeyecek değer (modelin sınırı daha küçükse o)
    query_prefix: str = ""
    doc_prefix: str = ""
    dtype: str | None = None  # None: modelin kendi ayarı; "float32": CPU'da tam hassasiyet zorla


# Embedding modelleri. Varsayılan bge-m3; diğer ikisi bellek karşılaştırması için küçük modeller.
#  - bge-m3: 568M parametre, 1024 boyut, 8192 token. Ön ek gerektirmez.
#  - granite-97m: IBM Granite Embedding 97M Multilingual R2 (2026), 384 boyut, 32K token,
#    Türkçe "geliştirilmiş destek" listesinde. Model kartındaki örnekler ön eksiz.
#  - e5-small: intfloat/multilingual-e5-small, 118M, 384 boyut, en fazla 512 token; model kartı
#    "query: " / "passage: " ön eklerini zorunlu tutar. 512'den uzun parçalar kesilir.
EMBED_MODELS = {
    "bge-m3": EmbedSpec("bge-m3", "BAAI/bge-m3", 2048),
    "granite-97m": EmbedSpec("granite-97m", "ibm-granite/granite-embedding-97m-multilingual-r2", 2048),
    # Granite'ın yapılandırması bfloat16; CPU'da bu hassasiyetle yükleniyor (sentence-transformers
    # uyarısı). Karşılaştırma için float32 sürümü ayrı bir yapılandırma olarak ölçülür.
    "granite-97m-fp32": EmbedSpec("granite-97m-fp32", "ibm-granite/granite-embedding-97m-multilingual-r2",
                                  2048, dtype="float32"),
    "e5-small": EmbedSpec("e5-small", "intfloat/multilingual-e5-small", 512, "query: ", "passage: "),
}
DEFAULT_EMBED = "bge-m3"
# Geriye uyumluluk
EMBED_MODEL = EMBED_MODELS[DEFAULT_EMBED].name
EMBED_MAX_TOKENS = EMBED_MODELS[DEFAULT_EMBED].max_tokens


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
