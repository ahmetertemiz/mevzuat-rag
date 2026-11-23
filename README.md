# mevzuat-rag

Türk e-ticaret ve tüketici mevzuatı üzerinde **kaynak göstererek** soru cevaplayan bir araç (RAG).
Bu depo şu an yalnızca belge işleme ve arama katmanını hedefliyor; cevap üretimi sonraki aşamada.

## Kapsam (docs_raw/)

| Dosya | Belge |
|---|---|
| `1.5.6502.pdf` | 6502 sayılı Tüketicinin Korunması Hakkında Kanun (TKHK) |
| `1.5.6563.pdf` | 6563 sayılı Elektronik Ticaretin Düzenlenmesi Hakkında Kanun (ETK) |
| `1.5.6698.pdf` | 6698 sayılı Kişisel Verilerin Korunması Kanunu (KVKK) |
| `7.5.20237.pdf` | Mesafeli Sözleşmeler Yönetmeliği (MSY) |

Kaynak: mevzuat.gov.tr, indirme tarihi 2026-11-23. `docs_raw/` içindeki dosyalar değiştirilmez.

## Tasarım özeti

- **Parçalama:** madde bazlı; uzun maddeler fıkra, gerekirse bent sınırından bölünür. Her parça
  belge, madde no, madde başlığı, fıkra aralığı, dipnotlar ve değişiklik notlarıyla birlikte tutulur.
- **Varsayılan arama:** BM25 + sorgu yeniden yazımı. Soru bir model çağrısıyla mevzuat diline
  çevrilmiş 2-4 sorguya dönüştürülür; özgün soru ve üretilen sorgular ayrı ayrı aranıp RRF ile
  birleştirilir. Çağrı başarısız olursa düz BM25'e düşülür ve sonuç bunu belirtir.
  torch ve embedding modeli gerekmez.
- **İsteğe bağlı:** embedding (`bge-m3` vb.) ile yoğun ve hibrit arama (`requirements-embedding.txt`).
- **Depolama:** veritabanı yok; `data/chunks.jsonl` (+ embedding kullanılırsa numpy dizisi).
- Çekirdek mantık `src/mevzuat_rag/` altında, arayüzden bağımsız.

## Kurulum

Üç bağımlılık dosyası var; yayın ortamı yalnızca ilkini kurar:

| Dosya | Ne için | Yayında |
|---|---|---|
| `requirements.txt` | Hazır `data/chunks.jsonl` ile BM25 + sorgu yeniden yazımı, testler | ✔ |
| `requirements-build.txt` | PDF'lerden `chunks.jsonl` üretmek (`pymupdf`) ve belge işleme testleri | ✘ |
| `requirements-embedding.txt` | Embedding modları, indeks kurma, deneyler, bellek ölçümleri (torch) | ✘ |

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m pip install -e .
.venv\Scripts\python -m pytest
```

Temiz bir ortamda yalnızca `requirements.txt` ile kurulum yaklaşık 130 MB tutar; PDF işleme ve
embedding testleri atlanır. Geliştirme için:

```powershell
.venv\Scripts\python -m pip install -r requirements-build.txt -r requirements-embedding.txt
```

Sorgu yeniden yazımı için proje kökünde `.env` dosyası: `ANTHROPIC_API_KEY=...` (git'e girmez).

## Belge işleme

```powershell
.venv\Scripts\python scripts\build_chunks.py
```

Çıktılar:

- `data/chunks.jsonl`: her satır bir parça. Önemli alanlar:
  - `metin`: resmî metin (değişiklik notları dahil)
  - `arama_metni`: bağlam başlığı + değişiklik notları temizlenmiş metin. Hem embedding hem BM25 bunu kullanır.
  - `dipnotlar`: `[{no, tur, konum, metin}]`. `tur`: `aym_karari`, `tablo_atfi`, `yururluk`, `atif`, `degisiklik_gecmisi`. `konum`: madde başlığı / madde girişi / fıkra n. Cevap üretiminde modele bu alan verilecek.
  - `indekse_dahil`: arama indeksine girip girmeyeceği.
- `data/belgeler.json`: belge üstverisi (RG bilgisi, indirme tarihi, son değişiklik bilgileri).
- `reports/dogrulama.md`: doğrulama raporu (sayımlar, uzunluklar, şüpheli parçalar, tablo kontrolü, örnekler).

Nasıl çalışır: PyMuPDF ile her satırın punto boyutu okunur. Gövde, dipnot ve üst simge dipnot işaretleri farklı puntoda olduğu için dipnotlar madde metninden ayrılır. Dipnot sayfa sonunda bir cümleyi bölse bile metin yeniden birleşir.

## Arama

```powershell
.venv\Scripts\python search.py "aldığım ürünü beğenmedim geri verebilir miyim"   # BM25 + yeniden yazım
.venv\Scripts\python search.py "6502 m.48" --yeniden-yazma -k 3                     # yalnız BM25, model çağrısı yok
```

Çıktı, yeniden yazımın durumunu (`uygulandı` / `kapalı` / `başarısız`), üretilen sorguları,
maliyeti ve başarısızlık durumunda uyarıyı gösterir. Kod içinden: `mevzuat_rag.pipeline.Arayici`.

- **BM25:** Türkçe küçük harf + ilk 5 harf kırpma (F5) + küçük bir durak kelime listesi.
  Madde numaraları özel belirtece çevrilir: `md:48`, `md:47/a`, `md:ek1`, `md:gecici2` ve belge
  adıyla birleşik `md:tkhk:48`. Bu belirteçler yalnızca sorguda ve parçanın bağlam başlığında
  üretilir. Gövdedeki "48 inci maddesinin" gibi atıflar belirtece çevrilmez.
- **Sorgu yeniden yazımı** (`src/mevzuat_rag/rewrite.py`, prompt v3): model `REWRITE_MODEL` (şu an
  `claude-haiku-5-5`, sunucu tarafı fallback yok), effort `low`, JSON çıktı, istemci zaman aşımı 20 sn. Çok konulu sorularda her
  konu için en az bir sorgu, en fazla 4. Sorgular yalnız konu ve kavram içerir: soruda geçmeyen
  sayı (süre, tutar, oran, tarih, kanun/madde numarası) yazılmaz; yazılırsa kod o sorguyu atar ve
  `SearchResult.atilan_sorgular` alanında belirtir. Prompt değişince `PROMPT_VERSION` artırılır.
- **Birleştirme:** Reciprocal Rank Fusion, `k=60`, ağırlık yok. Skoru 0 olan BM25 sonuçları
  birleşime girmez.

### Embedding (isteğe bağlı)

```powershell
.venv\Scripts\python scripts\build_index.py --model bge-m3      # index/bge-m3/ (ilk çalıştırmada model iner)
.venv\Scripts\python search.py "cayma hakkı" --mode hybrid --model bge-m3
```

Modeller: `bge-m3`, `granite-97m`, `granite-97m-fp32`, `e5-small`. Bellek ve süre:
`reports/performans_<model>.md` (`scripts\benchmark_model.py --model <model>`).

## Değerlendirme

```powershell
.venv\Scripts\python scripts\eval_retrieval.py                                   # dense / bm25 / hybrid (embedding kurulumu ister)
.venv\Scripts\python scripts\eval_retrieval.py --varsayilan                      # varsayılan hat, canlı model çağrısı
```

- `evals/retrieval.yaml`: 30 soruluk geliştirme seti (25'i arama kodu yazılmadan, 5 madde numarası
  sorusu sonraki deneylerden önce commit'lendi). Seçenek karşılaştırmaları bu sette yapılır.
- `evals/holdout.yaml`: holdout seti. Soruları proje sahibi yazar; seçilen yapılandırma bir kez
  koşulur: `scripts\eval_retrieval.py --set evals/holdout.yaml --varsayilan`.
- Sonuçlar: [evals/RAPOR.md](evals/RAPOR.md) (yöntemler),
  [evals/DENEYLER.md](evals/DENEYLER.md) (modeller × hibrit × yeniden yazım, bellek, süre, maliyet),
  [evals/MODEL_KARSILASTIRMA.md](evals/MODEL_KARSILASTIRMA.md) (yeniden yazım modeli, 3'er koşu),
  [evals/RAPOR_retrieval_varsayilan.md](evals/RAPOR_retrieval_varsayilan.md) (varsayılan hat, tek koşu).

## Bilinen sınırlar

- **İdari para cezası tabloları** (6502 m.77 ve 6563 m.12, 2026 tutarları) PDF görüntüleriyle
  karşılaştırıldı, onaylandı ve indekste. İki tabloda da bazı satırlarda aynı fıkra için birden çok
  tutar var; hangi tutarın hangi duruma ait olduğu tabloda yazmaz, ilgili maddenin (6502 m.77,
  6563 m.12) metnindedir. Her iki tablo parçasının başında bu not yer alır. Her satır `ilgili_parca` alanıyla karşılık geldiği madde
  parçasına bağlıdır.
- **Ceza tutarı soruları (cevap üretimi için kural):** tablo parçası **tek başına kullanılmaz**.
  Tablo parçası getirildiğinde `ilgili_parcalar` / satırdaki `ilgili_parca` üzerinden 77. maddenin
  (6563 için 12. maddenin) ilgili fıkrası da modele verilir. Tutarın hangi duruma ait olduğu madde
  metninden çıkmıyorsa araç tutarları sıralar ve "hangisinin geçerli olduğu 77. maddeye göre
  belirlenir" der. Ayrıntı: [docs/cevap_uretimi_notlari.md](docs/cevap_uretimi_notlari.md).
- **Dışarıda bırakılanlar:** kanunların sonundaki değişiklik/yürürlük tarihleri listeleri, KVKK
  kadro cetveli, yönetmeliğin Resmî Gazete listesi (bu listenin son satırı yalnızca üstveriye işlendi).
- **Mülga maddeler** kısa bir kayıt olarak indekste kalır (tarih ve dayanakla). Fıkra düzeyinde mülga
  hükümler madde metninin içinde durur.
- **Başlık dipnotları** (ör. 6502 m.77'nin 25–27 numaralı dipnotları) maddenin her parçasına kopyalanır.
  Cevap üretiminde dipnotlar `(belge, no)` ile tekilleştirilmeli.
- **Ayrıştırma bu dört PDF'in biçimine göre ayarlandı.** Punto farkı, `MADDE n –` kalıbı ve ek
  başlıkları buna dahil. Yeni bir belge eklenirse doğrulama raporu yeniden incelenmeli.
- **Yeniden yazım koşudan koşuya değişir.** Aynı model ve prompt ile geliştirme setinde @5,
  cevaplı 26 soruda 22 ile 25 arasında oynadı (Opus 5.5, 4 koşu). Tek koşuluk bir sonuç (holdout
  dahil) bu oynama payıyla okunmalı.
- **Yeniden yazılmış sorgular bilgi içerebilir** (ör. yanlış bir süre). Arama için kullanılırlar;
  cevap üretiminde modele verilmemelidir.
- **Varsayılan hat API'ye bağlıdır.** Çağrı başarısız olursa düz BM25'e düşülür; düz BM25 günlük dil
  sorularında belirgin biçimde zayıftır (geliştirme setinde 3/8).
- **Tarih kapsamı:** metinler mevzuat.gov.tr'den 2026-11-23'te indirildi. Bu tarihten sonraki değişiklikleri içermez.
