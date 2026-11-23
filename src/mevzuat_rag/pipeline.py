"""Varsayılan arama hattı: BM25 + sorgu yeniden yazımı, düşme davranışıyla.

    arayici = Arayici()
    sonuc = arayici.ara("aldığım ürünü beğenmedim geri verebilir miyim")
    sonuc.hits          # parçalar
    sonuc.yeniden_yazim # "uygulandı" | "kapalı" | "başarısız"
    sonuc.uyari         # başarısızsa kullanıcıya gösterilecek açıklama

Yeniden yazım çağrısı herhangi bir nedenle başarısız olursa (anahtar yok, ağ hatası, zaman aşımı,
reddetme, boş/bozuk çıktı) arama düz BM25 ile yapılır ve sonuç bunu belirtir; hata yukarı fırlatılmaz.

Embedding modları (dense / hybrid) isteğe bağlıdır ve requirements-embedding.txt ile kurulur.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from . import config
from .retrieve import Hit, Retriever

UYGULANDI, KAPALI, BASARISIZ = "uygulandı", "kapalı", "başarısız"


@dataclass
class SearchResult:
    soru: str
    hits: list[Hit]
    mode: str
    yeniden_yazim: str
    sorgular: list[str] = field(default_factory=list)
    uyari: str | None = None
    maliyet_usd: float = 0.0
    yeniden_yazim_sn: float | None = None
    # Sayı denetiminde atılan sorgular: [{"sorgu", "neden"}] (rewrite.sayi_denetimi)
    atilan_sorgular: list[dict] = field(default_factory=list)


class Arayici:
    def __init__(self, mode: str = config.DEFAULT_SEARCH_MODE, rewrite: bool = config.DEFAULT_REWRITE,
                 embed_model: str = config.DEFAULT_EMBED, rewrite_model: str | None = None,
                 retriever: Retriever | None = None, rewriter=None):
        self.mode = mode
        self.rewrite = rewrite
        self.retriever = retriever or Retriever(model=embed_model, load_model=mode != "bm25")
        self._rewriter = rewriter
        self._rewriter_error: str | None = None
        self.rewrite_model = rewrite_model

    def _get_rewriter(self):
        if self._rewriter is None and self._rewriter_error is None:
            try:
                from .rewrite import REWRITE_MODEL, QueryRewriter
                self._rewriter = QueryRewriter(model=self.rewrite_model or REWRITE_MODEL)
            except Exception as e:  # anthropic kurulu değil, anahtar yok vb.
                self._rewriter_error = f"{type(e).__name__}: {e}"
        return self._rewriter

    def ara(self, soru: str, k: int = 5) -> SearchResult:
        if not self.rewrite:
            return SearchResult(soru, self.retriever.search(soru, k=k, mode=self.mode), self.mode, KAPALI)

        sorgular: list[str] = []
        atilan: list[dict] = []
        uyari = None
        maliyet, sure = 0.0, None
        rw = self._get_rewriter()
        if rw is None:
            uyari = f"Sorgu yeniden yazımı kullanılamadı ({self._rewriter_error}); düz arama yapıldı."
        else:
            try:
                r = rw.rewrite(soru)
                maliyet, sure = r.cost_usd, r.seconds
                atilan = list(getattr(r, "atilan_sorgular", []) or [])
                if r.sorgular:
                    sorgular = r.sorgular
                elif atilan:
                    uyari = ("Üretilen sorguların hepsi sayı denetiminde atıldı (soruda olmayan sayı "
                             "içeriyorlardı); düz arama yapıldı.")
                else:
                    uyari = (f"Sorgu yeniden yazımı sorgu üretmedi (stop_reason={r.stop_reason}); "
                             "düz arama yapıldı.")
            except Exception as e:  # ağ, zaman aşımı, API hatası, beklenmeyen çıktı
                uyari = f"Sorgu yeniden yazımı başarısız oldu ({type(e).__name__}); düz arama yapıldı."

        hits = self.retriever.search(soru, k=k, mode=self.mode, extra_queries=sorgular or None)
        return SearchResult(soru, hits, self.mode, UYGULANDI if sorgular else BASARISIZ,
                            sorgular, uyari, maliyet, sure, atilan)
