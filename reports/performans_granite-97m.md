# granite-97m performans ölçümü

`python scripts/benchmark_model.py --model granite-97m` ile üretildi. Tek süreç, yalnız CPU.

## Ortam

- İşletim sistemi: Windows-11-10.0.26200-SP0
- İşlemci: Intel64 Family 6 Model 186 Stepping 2, GenuineIntel · mantıksal çekirdek: 20 · torch iş parçacığı: 14
- Toplam RAM: 31.7 GB
- Python 3.12.10 · torch 2.15.0+cpu · sentence-transformers 6.3.0
- Model: `ibm-granite/granite-embedding-97m-multilingual-r2` · 97M parametre · boyut 384 · max_seq_length 2048 (en uzun parça 1362 token, kesilen: yok)
- Diskteki model önbelleği: 0.21 GB

## Bellek (RSS)

| Aşama | Değer |
|---|---|
| Süreç başlangıcı | 22 MB |
| torch + sentence-transformers import sonrası artış | +360 MB |
| Model yükleme artışı | +233 MB |
| Model yüklü, boşta | 616 MB |
| **Sorgu sırasında tepe (yayın senaryosu)** | **632 MB** |
| İndeks kurarken tepe (217 parça; yayında gerekmez) | 850 MB |

## Süreler

| Aşama | Süre |
|---|---|
| import (torch + sentence-transformers) | 6.9 sn |
| Model yükleme (önbellekten) | 1.0 sn |
| Soğuk başlangıç toplamı (import + yükleme) | 7.9 sn |
| Tüm parçaların embedding'i (217) | 139.3 sn (642 ms/parça) |

Sorgu başına (30 soru × 3 tekrar = 90 ölçüm; medyan / p95 / en kötü):

| İşlem | ms |
|---|---|
| Sorgu embedding'i + benzerlik (dense) | 45 / 82 / 98 |
| BM25 | 1 / 1 / 2 |
| Hibrit arama toplamı (dense + BM25 + RRF) | 47 / 92 / 113 |

## Notlar

- Sorgu sırasındaki tepe, "model yüklü, boşta" satırından yüksektir: ağırlıklar (safetensors) belleğe eşlenerek açılır ve ilk embedding'de sayfalanır. Yayın için ölçü alınacak satır budur.
- Sorgu süresinin neredeyse tamamı sorgu embedding'inden gelir; BM25 ve RRF ihmal edilebilir.
- İndeks yayında yeniden hesaplanmaz, dosyadan okunur; indeks kurma yalnızca belgeler değişince gerekir.
- Diskteki önbellek Windows'ta sembolik bağlantı olmadığı için dosya kopyalarını içerir; Linux'ta daha küçük olması beklenir.
- Soğuk başlangıç süresi, ücretsiz barındırma ortamlarında (uyku sonrası uyanma) kullanıcının beklediği süreye doğrudan eklenir.
