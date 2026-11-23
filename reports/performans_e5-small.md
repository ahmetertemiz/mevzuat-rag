# e5-small performans ölçümü

`python scripts/benchmark_model.py --model e5-small` ile üretildi. Tek süreç, yalnız CPU.

## Ortam

- İşletim sistemi: Windows-11-10.0.26200-SP0
- İşlemci: Intel64 Family 6 Model 186 Stepping 2, GenuineIntel · mantıksal çekirdek: 20 · torch iş parçacığı: 14
- Toplam RAM: 31.7 GB
- Python 3.12.10 · torch 2.15.0+cpu · sentence-transformers 6.3.0
- Model: `intfloat/multilingual-e5-small` · 118M parametre · boyut 384 · max_seq_length 512 (en uzun parça 1027 token, kesilen: ['TKHK-m3-1', 'TKHK-m4-1', 'TKHK-m5-1', 'TKHK-m11-1', 'TKHK-m34-1', 'TKHK-m47-1', 'TKHK-m48-1', 'TKHK-m49-1', 'TKHK-m51-1', 'TKHK-m63-1', 'TKHK-m70-1', 'TKHK-m77-2', 'TKHK-m77-6', 'TKHK-m77-7', 'TKHK-tablo2026-1', 'ETK-m2-1', 'ETK-m11-1', 'ETK-m12-1', 'ETK-m12-2', 'ETK-m12-4', 'ETK-ek2-2', 'ETK-ek2-3', 'ETK-ek2-4', 'ETK-ek2-5', 'ETK-ek4-1', 'ETK-ek4-2', 'ETK-tablo2026-1', 'KVKK-m21-1', 'MSY-m4-1', 'MSY-m5-1', 'MSY-m6-1', 'MSY-m12-1', 'MSY-m12a-1', 'MSY-m15-1'])
- Diskteki model önbelleği: 0.46 GB

## Bellek (RSS)

| Aşama | Değer |
|---|---|
| Süreç başlangıcı | 22 MB |
| torch + sentence-transformers import sonrası artış | +359 MB |
| Model yükleme artışı | +782 MB |
| Model yüklü, boşta | 1164 MB |
| **Sorgu sırasında tepe (yayın senaryosu)** | **1179 MB** |
| İndeks kurarken tepe (217 parça; yayında gerekmez) | 1320 MB |

## Süreler

| Aşama | Süre |
|---|---|
| import (torch + sentence-transformers) | 6.8 sn |
| Model yükleme (önbellekten) | 2.7 sn |
| Soğuk başlangıç toplamı (import + yükleme) | 9.5 sn |
| Tüm parçaların embedding'i (217) | 8.8 sn (41 ms/parça) |

Sorgu başına (30 soru × 3 tekrar = 90 ölçüm; medyan / p95 / en kötü):

| İşlem | ms |
|---|---|
| Sorgu embedding'i + benzerlik (dense) | 14 / 18 / 21 |
| BM25 | 1 / 1 / 2 |
| Hibrit arama toplamı (dense + BM25 + RRF) | 15 / 19 / 28 |

## Notlar

- Sorgu sırasındaki tepe, "model yüklü, boşta" satırından yüksektir: ağırlıklar (safetensors) belleğe eşlenerek açılır ve ilk embedding'de sayfalanır. Yayın için ölçü alınacak satır budur.
- Sorgu süresinin neredeyse tamamı sorgu embedding'inden gelir; BM25 ve RRF ihmal edilebilir.
- İndeks yayında yeniden hesaplanmaz, dosyadan okunur; indeks kurma yalnızca belgeler değişince gerekir.
- Diskteki önbellek Windows'ta sembolik bağlantı olmadığı için dosya kopyalarını içerir; Linux'ta daha küçük olması beklenir.
- Soğuk başlangıç süresi, ücretsiz barındırma ortamlarında (uyku sonrası uyanma) kullanıcının beklediği süreye doğrudan eklenir.
