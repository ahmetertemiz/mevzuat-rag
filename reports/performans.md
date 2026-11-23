# bge-m3 performans ölçümü

`python scripts/benchmark_model.py` ile üretildi. Tek süreç, yalnız CPU.

## Ortam

- İşletim sistemi: Windows-11-10.0.26200-SP0
- İşlemci: Intel64 Family 6 Model 186 Stepping 2, GenuineIntel · mantıksal çekirdek: 20 · torch iş parçacığı: 14
- Toplam RAM: 31.7 GB
- Python 3.12.10 · torch 2.15.0+cpu · sentence-transformers 6.3.0
- Model: `BAAI/bge-m3` · boyut 1024 · max_seq_length 2048 (en uzun parça 1025 token, kesilen: yok)
- Diskteki model önbelleği: 4.25 GB

## Bellek (RSS)

| Aşama | Değer |
|---|---|
| Süreç başlangıcı | 21 MB |
| torch + sentence-transformers import sonrası artış | +360 MB |
| Model yükleme artışı | +339 MB |
| Model yüklü, boşta | 721 MB |
| İndeks kurarken tepe (217 parça) | 2297 MB |
| Sorgu sırasında tepe | 2022 MB |

## Süreler

| Aşama | Süre |
|---|---|
| import (torch + sentence-transformers) | 7.4 sn |
| Model yükleme (önbellekten) | 2.6 sn |
| Soğuk başlangıç toplamı (import + yükleme) | 10.0 sn |
| Tüm parçaların embedding'i (217) | 116.0 sn (535 ms/parça) |

Sorgu başına (25 soru × 3 tekrar = 75 ölçüm; medyan / p95 / en kötü):

| İşlem | ms |
|---|---|
| Sorgu embedding'i + benzerlik (dense) | 76 / 96 / 100 |
| BM25 | 1 / 1 / 1 |
| Hibrit arama toplamı (dense + BM25 + RRF) | 76 / 99 / 100 |

## Yayın açısından yorum

- **Gerçek bellek ihtiyacı "model yüklü, boşta" satırı değil, sorgu sırasındaki tepedir.** Ağırlıklar (safetensors) belleğe eşlenerek açılır ve ilk embedding'de sayfalanır; bu yüzden yükleme anında RSS düşük görünür, ilk sorgudan sonra model ağırlıklarının tamamı (fp32, ~2,2 GB) bellektedir. Yayın ortamında süreç başına ~2,5 GB RAM ayrılmalı.
- Sorgu süresinin neredeyse tamamı sorgu embedding'inden gelir; BM25 ve RRF ihmal edilebilir.
- ~200 parçalık indeks (float32, 1024 boyut) yaklaşık 1 MB'tır; indeks yayında yeniden hesaplanmaz, dosyadan okunur. İndeks kurma (~2 dk) yalnızca belgeler değişince gerekir.
- Diskteki önbellek, Windows'ta sembolik bağlantı kullanılamadığı için dosyaların kopyalanmasından dolayı model boyutunun yaklaşık iki katıdır; Linux'ta yaklaşık yarısı beklenir.
- Soğuk başlangıç süresi, ücretsiz barındırma ortamlarında (uyku sonrası uyanma) kullanıcının beklediği süreye doğrudan eklenir.
