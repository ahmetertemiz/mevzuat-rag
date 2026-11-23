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
- **Arama:** `BAAI/bge-m3` (yerel, çok dilli) + BM25, Reciprocal Rank Fusion ile birleştirilir.
- **Depolama:** veritabanı yok; `data/chunks.jsonl` + numpy dizisi.
- Çekirdek mantık `src/mevzuat_rag/` altında, arayüzden bağımsız.

## Kurulum

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m pip install -e .
.venv\Scripts\python -m pytest
```

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

## Bilinen sınırlar

- **İdari para cezası tabloları** (6502 m.77 ve 6563 m.12, 2026 tutarları) PDF görüntüleriyle
  karşılaştırıldı, onaylandı ve indekste. 6502 tablosunda bazı satırlarda aynı fıkra için birden çok
  tutar var; hangi tutarın hangi duruma ait olduğu tabloda yazmaz, 77. maddenin metnindedir. Tablo
  parçasının başında bu not yer alır. Her satır `ilgili_parca` alanıyla karşılık geldiği madde
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
- **Tarih kapsamı:** metinler mevzuat.gov.tr'den 2026-11-23'te indirildi. Bu tarihten sonraki değişiklikleri içermez.
