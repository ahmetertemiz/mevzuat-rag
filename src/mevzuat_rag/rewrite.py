"""Sorgu yeniden yazımı: kullanıcı sorusunu, aramadan önce bir model çağrısıyla mevzuat diline
çevrilmiş 2-4 arama sorgusuna dönüştürür. Model soruyu CEVAPLAMAZ; yalnızca sorgu üretir.

Özgün soru ve üretilen sorgular retrieve.Retriever.search(..., extra_queries=...) ile ayrı ayrı
aranır, sıralamalar RRF ile birleştirilir.

API anahtarı .env dosyasından (ANTHROPIC_API_KEY) okunur; hiçbir yere yazdırılmaz.
Değerlendirmede tekrarlanabilirlik ve maliyet için sonuçlar evals/cache/ altında önbelleğe alınır.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from . import config

REWRITE_MODEL = "claude-opus-5-5"
REWRITE_EFFORT = "low"
MAX_QUERIES = 4
# Prompt değiştiğinde artırılır; önbellek dosya adına girer ki eski prompt'un çıktıları kullanılmasın.
#  1: ilk sürüm (2-3 sorgu)
#  2: çok konulu / çok alt sorulu sorularda her konu için en az bir sorgu, en fazla 4 sorgu
PROMPT_VERSION = 2
# $/1M token (claude-api referansı, 2026-11-03 önbelleği). Maliyet hesabı içindir.
PRICES = {
    "claude-opus-5-5": (4.00, 20.00),
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-haiku-5-5": (0.10, 0.50),
}

SYSTEM_PROMPT = """Sen Türk tüketici hukuku, elektronik ticaret, mesafeli sözleşmeler ve kişisel \
verilerin korunması mevzuatında arama yapan bir sistemin sorgu yazarısın.

Görevin: kullanıcının sorusunu CEVAPLAMADAN, ilgili kanun ve yönetmelik maddelerini bulmaya \
yarayacak kısa arama sorguları üretmek. Genellikle 2 ya da 3 sorgu yeterlidir; en fazla 4 sorgu yaz.

Kurallar:
- Sorguları mevzuatta geçmesi muhtemel hukuki terimlerle yaz (örneğin "iade etmek" yerine \
duruma göre "cayma hakkı", "sözleşmeden dönme" ya da "ayıplı mal"; "mesaj" yerine "ticari \
elektronik ileti").
- Soru birden çok konu ya da alt soru içeriyorsa (ör. "... yapabilir miyim, ... ne kadar sürede?") her konu ve her alt soru için en az bir sorgu yaz; hiçbir alt soruyu sorgusuz bırakma. Toplam sorgu sayısı yine en fazla 4 olsun.
- Soruda kanun numarası, kanun adı ya da madde numarası geçiyorsa bunları sorgulardan en az \
birinde aynen koru. Soruda olmayan madde numarası uydurma.
- Soru bu mevzuatın dışında görünse bile reddetme; konuyu hukuki terimlerle anlatan sorgular üret.
- Sorgular kısa olsun (en fazla 12 kelime), açıklama ya da cevap içermesin.

Örnekler:
Soru: Spor salonu üyeliğimi iptal ettirmek istiyorum ama sözleşmede bir yıl yazıyor.
Sorgular: ["abonelik sözleşmesinin feshi", "belirli süreli abonelik sözleşmesinde tüketicinin fesih hakkı"]

Soru: Bankadan çektiğim krediyi vaktinden önce kapatırsam faizden indirim yapılır mı?
Sorgular: ["tüketici kredisi erken ödeme faiz indirimi", "belirli süreli kredi sözleşmesinde erken ödeme"]

Soru: Rafta yazan fiyat ile kasada ödediğim fiyat farklı çıktı.
Sorgular: ["fiyat etiketi ile satış fiyatı arasındaki fark", "etiket fiyatı tüketici lehine olan fiyat"]

Soru: Aldığım paket turun programını değiştirdiler. Sözleşmeden dönebilir miyim, ödediğim parayı ne kadar sürede geri alırım?
Sorgular: ["paket tur sözleşmesinde değişiklik", "paket tur sözleşmesinden dönme hakkı", "paket tur bedelinin iadesi süresi"]

Soru: 6698 sayılı kanunun 9. maddesi yurt dışına aktarımı nasıl düzenliyor?
Sorgular: ["6698 sayılı Kanun madde 9", "kişisel verilerin yurt dışına aktarılması yeterlilik kararı"]
"""

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "sorgular": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["sorgular"],
    "additionalProperties": False,
}


@dataclass
class Rewrite:
    soru: str
    sorgular: list[str]
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    seconds: float
    stop_reason: str


def load_dotenv(path: Path = config.ROOT / ".env") -> None:
    """Basit .env okuyucu: ANAHTAR=değer satırlarını, ortamda yoksa ortama ekler. Değer yazdırılmaz."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


class QueryRewriter:
    def __init__(self, model: str = REWRITE_MODEL, effort: str = REWRITE_EFFORT):
        import anthropic

        load_dotenv()
        self.client = anthropic.Anthropic()
        self.model = model
        self.effort = effort

    def rewrite(self, question: str) -> Rewrite:
        t0 = time.perf_counter()
        resp = self.client.beta.messages.create(
            model=self.model,
            max_tokens=4000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": f"Soru: {question}"}],
            output_config={"effort": self.effort,
                           "format": {"type": "json_schema", "schema": OUTPUT_SCHEMA}},
            # Güvenlik sınıflandırıcısı reddederse istek sunucu tarafında başka modelde yeniden
            # çalışır (Opus 5.5 için önerilen varsayılan).
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        )
        dt = time.perf_counter() - t0
        queries: list[str] = []
        if resp.stop_reason != "refusal":
            text = next((b.text for b in resp.content if b.type == "text"), "")
            try:
                queries = [q.strip() for q in json.loads(text).get("sorgular", []) if q.strip()][:MAX_QUERIES]
            except json.JSONDecodeError:
                queries = []
        pin, pout = PRICES.get(self.model, (0.0, 0.0))
        u = resp.usage
        cost = (u.input_tokens * pin + u.output_tokens * pout) / 1e6
        return Rewrite(question, queries, self.model, u.input_tokens, u.output_tokens,
                       round(cost, 6), round(dt, 3), resp.stop_reason or "")


def cache_path(model: str = REWRITE_MODEL) -> Path:
    return config.ROOT / "evals" / "cache" / f"rewrites_{model}_p{PROMPT_VERSION}.json"


class RewriteCache:
    """Soru metni -> Rewrite. Aynı soru için model bir kez çağrılır."""

    def __init__(self, path: Path):
        self.path = path
        self.data: dict[str, dict] = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}

    def get_or_create(self, question: str, rewriter: QueryRewriter | None) -> Rewrite:
        if question in self.data:
            return Rewrite(**self.data[question])
        if rewriter is None:
            raise KeyError(f"önbellekte yok ve model çağrısı kapalı: {question!r}")
        r = rewriter.rewrite(question)
        self.data[question] = asdict(r)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
        return r
