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
import re
import time
from dataclasses import asdict, dataclass, field
from functools import lru_cache
from pathlib import Path

from . import config
from .textnorm import normalize

REWRITE_MODEL = "claude-haiku-5-5"  # karar 2026-11-23: model karşılaştırması (evals/MODEL_KARSILASTIRMA.md)
REWRITE_EFFORT = "low"
MAX_QUERIES = 4
# Prompt değiştiğinde artırılır; önbellek dosya adına girer ki eski prompt'un çıktıları kullanılmasın.
#  1: ilk sürüm (2-3 sorgu)
#  2: çok konulu / çok alt sorulu sorularda her konu için en az bir sorgu, en fazla 4 sorgu
#  3: sorgular yalnız konu ve kavram içerir; soruda geçmeyen sayı (süre, tutar, oran, tarih, kanun ve
#     madde numarası) eklenmez. Ayrıca kodda denetim (sayi_denetimi): böyle bir sorgu atılır.
PROMPT_VERSION = 3
SERVER_FALLBACK_MODELS = {"claude-opus-5-5", "claude-sonnet-5-5"}
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
birinde aynen koru.
- Sorgular yalnızca konu ve kavram içersin. Soruda geçmeyen hiçbir sayı ekleme: süre ("on dört \
gün", "30 gün"), tutar, oran, tarih, kanun numarası ya da madde numarası yazma. Cevabı tahmin \
etmeye çalışma; "kaç gün" diye soruluyorsa sorguya süreyi değil, sürenin konusunu yaz \
(ör. "cayma hakkı süresi"). Soruda olmayan sayı içeren sorgular sistem tarafından atılır.
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
    atilan_sorgular: list[dict] = field(default_factory=list)  # [{"sorgu", "neden"}]


# ------------------------------------------------------------------ sayı denetimi
#
# Model cevabı tahmin edip sorguya süre / madde numarası ekleyebilir ("cayma süresi on gün").
# Soruda geçmeyen bir sayı içeren sorgu atılır. Rakamlar ve yazıyla yazılmış süre/tutar/oran
# kalıpları ("on dört gün", "yüzde on", "otuz bin lira") denetlenir. Soruda aynen geçen sayılar serbest.

_NUM_WORDS = (r"bir|iki|üç|dört|beş|altı|yedi|sekiz|dokuz|on|yirmi|otuz|kırk|elli|altmış|yetmiş|"
              r"seksen|doksan|yüz|bin|milyon|milyar")
_UNITS = r"iş\s+günü|gün|hafta|ay|yıl|saat|dakika|lira|tl|kuruş"
_SUFFIX = r"(?:lık|lik|luk|lük|da|de|ta|te|dan|den|tan|ten|ı|i|u|ü|a|e)?"  # aylık, günde, yılı...
_SPELLED = re.compile(rf"\b(?:(?:{_NUM_WORDS})\s+)+(?:{_UNITS}){_SUFFIX}\b|\byüzde\s+(?:(?:{_NUM_WORDS})\b\s*)+")
_DIGITS = re.compile(r"\d+")


@lru_cache(maxsize=1)
def belge_kaydi_serbest() -> tuple[frozenset[str], tuple[str, ...]]:
    """Belge kaydındaki (data/belgeler.json) kanun numaraları ile belge adları ve kısaltmaları.
    Bunlar cevap tahmini değil, belge kimliğidir; sorguda geçmeleri serbesttir
    (ör. soru "KVKK" derken sorgunun "6698 sayılı Kanun" demesi)."""
    try:
        docs = json.loads(config.DOCS_META_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return frozenset(), ()
    numaralar = frozenset(d["numara"] for d in docs if d.get("tur") == "kanun")
    adlar = [normalize(x) for d in docs for x in (d.get("tam_ad"), d.get("belge_adi"), d.get("kisa_ad")) if x]
    return numaralar, tuple(sorted(set(adlar), key=len, reverse=True))


def sayi_denetimi(soru: str, sorgu: str) -> str | None:
    """Sorguda soruda geçmeyen bir sayı varsa nedenini döndürür, yoksa None.
    Belge kaydındaki kanun numaraları, belge adları ve kısaltmaları serbesttir."""
    serbest_no, serbest_ad = belge_kaydi_serbest()
    q, s = normalize(soru), normalize(sorgu)
    for ad in serbest_ad:  # belge adları sayı denetimine girmez
        s = s.replace(ad, " ")
    soru_rakam = set(_DIGITS.findall(q)) | serbest_no
    yeni = [d for d in _DIGITS.findall(s) if d not in soru_rakam]
    if yeni:
        return f"soruda olmayan sayı: {', '.join(yeni)}"
    yazili = [m.group(0).strip() for m in _SPELLED.finditer(s) if m.group(0).strip() not in q]
    if yazili:
        return f"soruda olmayan süre/tutar/oran: {', '.join(yazili)}"
    return None


def denetle(soru: str, sorgular: list[str]) -> tuple[list[str], list[dict]]:
    kalan, atilan = [], []
    for sg in sorgular:
        neden = sayi_denetimi(soru, sg)
        if neden:
            atilan.append({"sorgu": sg, "neden": neden})
        else:
            kalan.append(sg)
    return kalan, atilan


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


# Prompt v4 (deney seçeneği 3): v3'e tek bir genel kural eklenir. Belirli bir hukuki kavram eklenmez.
OZGUN_IFADE_KURALI = (
    "- Sorgulardan biri, kullanıcının sorusundaki kendi anahtar kelimelerini (ör. sorudaki ad ve "
    "fiilleri) olduğu gibi korusun; hukuki terime çevirme. Diğer sorgular hukuki terimlerle yazılır.\n")
SYSTEM_PROMPT_V4 = SYSTEM_PROMPT.replace("\n\nÖrnekler:\n", "\n" + OZGUN_IFADE_KURALI + "\nÖrnekler:\n", 1)


def sistem_promptu(surum: int = PROMPT_VERSION) -> str:
    if surum == 3:
        return SYSTEM_PROMPT
    if surum == 4:
        return SYSTEM_PROMPT_V4
    raise ValueError(f"desteklenmeyen prompt sürümü: {surum}")


class QueryRewriter:
    def __init__(self, model: str = REWRITE_MODEL, effort: str = REWRITE_EFFORT,
                 timeout: float = 20.0, max_retries: int = 2, prompt_surumu: int = PROMPT_VERSION):
        import anthropic

        load_dotenv()
        self.client = anthropic.Anthropic(timeout=timeout, max_retries=max_retries)
        self.model = model
        self.effort = effort
        self.prompt_surumu = prompt_surumu
        self.system = sistem_promptu(prompt_surumu)

    def rewrite(self, question: str) -> Rewrite:
        t0 = time.perf_counter()
        kwargs = dict(
            model=self.model,
            max_tokens=4000,
            system=getattr(self, "system", SYSTEM_PROMPT),
            messages=[{"role": "user", "content": f"Soru: {question}"}],
            output_config={"effort": self.effort,
                           "format": {"type": "json_schema", "schema": OUTPUT_SCHEMA}},
        )
        if self.model in SERVER_FALLBACK_MODELS:
            # Güvenlik sınıflandırıcısı reddederse istek sunucu tarafında başka modelde yeniden
            # çalışır (Opus 5.5 / Sonnet 5.5 için önerilen varsayılan).
            resp = self.client.beta.messages.create(
                **kwargs, betas=["server-side-fallback-2026-07-01"], fallbacks="default")
        else:
            # Haiku 5.5'te sunucu tarafı fallback yok; reddetme stop_reason ile ele alınır.
            resp = self.client.messages.create(**kwargs)
        dt = time.perf_counter() - t0
        queries: list[str] = []
        if resp.stop_reason != "refusal":
            text = next((b.text for b in resp.content if b.type == "text"), "")
            try:
                queries = [q.strip() for q in json.loads(text).get("sorgular", []) if q.strip()][:MAX_QUERIES]
            except json.JSONDecodeError:
                queries = []
        queries, dropped = denetle(question, queries)
        pin, pout = PRICES.get(self.model, (0.0, 0.0))
        u = resp.usage
        cost = (u.input_tokens * pin + u.output_tokens * pout) / 1e6
        return Rewrite(question, queries, self.model, u.input_tokens, u.output_tokens,
                       round(cost, 6), round(dt, 3), resp.stop_reason or "", dropped)


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
