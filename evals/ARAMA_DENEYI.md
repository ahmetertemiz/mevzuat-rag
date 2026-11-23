# Arama değişikliği deneyi

`python scripts/arama_deneyi.py` tarafından üretilir. Kural ve uygulama ayrıntıları ölçümden önce `docs/kararlar.md`'ye kaydedildi. k=8, 3 koşu; yeniden yazım Haiku 5.5. Hücreler: medyan (en düşük–en yüksek).

## 1. Sonuçlar

### Bağlam düzeyi (kural bu düzeyde uygulanır)

| Yapılandırma | dev1 (26) | dev2 (15) | Toplam (41) |
|---|---|---|---|
| 0 varsayılan | 24 (24–25) | 13 (12–13) | 37 |
| 1 iki aşamalı RRF | 25 (24–25) | 13 (12–13) | 38 |
| 2 parça çeşitliliği | 24 (24–25) | 13 (12–13) | 37 |
| 3 özgün ifade (prompt v4) | 24 (24–24) | 12 (12–13) | 36 |
| 4 = 1+2 | 25 (24–25) | 13 (13–13) | 38 |
| 5 = 1+2+3 | 25 (24–25) | 13 (13–13) | 38 |
| R bge-m3 hibrit, 1+2 | 25 (24–26) | 13 (12–13) | 38 |

### Arama düzeyi (@8, bilgi için)

| Yapılandırma | dev1 (26) | dev2 (15) | Toplam (41) |
|---|---|---|---|
| 0 varsayılan | 24 (24–25) | 11 (10–12) | 35 |
| 1 iki aşamalı RRF | 25 (24–25) | 12 (10–12) | 37 |
| 2 parça çeşitliliği | 24 (24–25) | 12 (10–12) | 36 |
| 3 özgün ifade (prompt v4) | 24 (24–24) | 11 (10–11) | 35 |
| 4 = 1+2 | 25 (24–25) | 12 (12–12) | 37 |
| 5 = 1+2+3 | 25 (24–25) | 12 (12–12) | 37 |
| R bge-m3 hibrit, 1+2 | 25 (24–26) | 13 (12–13) | 38 |

## 2. Karar kuralı

(a) toplamda varsayılana göre en az +3, (b) hiçbir sette −1'den fazla kayıp yok. Bağlam düzeyi, medyanlar.

| Yapılandırma | dev1 farkı | dev2 farkı | Toplam | (a) | (b) | Sonuç |
|---|---|---|---|---|---|---|
| 1 iki aşamalı RRF | +1 | +0 | +1 | ✗ | ✓ | ret |
| 2 parça çeşitliliği | +0 | +0 | +0 | ✗ | ✓ | ret |
| 3 özgün ifade (prompt v4) | +0 | -1 | -1 | ✗ | ✓ | ret |
| 4 = 1+2 | +1 | +0 | +1 | ✗ | ✓ | ret |
| 5 = 1+2+3 | +1 | +0 | +1 | ✗ | ✓ | ret |
| R bge-m3 hibrit, 1+2 | +1 | +0 | +1 | ✗ | ✓ | referans (seçilemez) |

**Seçilen:** hiçbiri — varsayılan değişmez

## 3. Kazanılan ve kaybedilen sorular (bağlam düzeyi, 3 koşunun çoğunluğu)

| Yapılandırma | Set | Kazanılan | Kaybedilen |
|---|---|---|---|
| 1 iki aşamalı RRF | dev1 | — | — |
| 1 iki aşamalı RRF | dev2 | — | A07 |
| 2 parça çeşitliliği | dev1 | — | — |
| 2 parça çeşitliliği | dev2 | — | — |
| 3 özgün ifade (prompt v4) | dev1 | — | S16 |
| 3 özgün ifade (prompt v4) | dev2 | — | A07 |
| 4 = 1+2 | dev1 | — | — |
| 4 = 1+2 | dev2 | — | — |
| 5 = 1+2+3 | dev1 | — | — |
| 5 = 1+2+3 | dev2 | A10 | A07 |
| R bge-m3 hibrit, 1+2 | dev1 | S06 | S26 |
| R bge-m3 hibrit, 1+2 | dev2 | A11 | A07 |

## 4. Yorum

- **Hiçbir yapılandırma kuralı sağlamadı; varsayılan (BM25 + yeniden yazım, prompt v3, düz RRF)
  değişmedi.** En iyi bağlam sonucu +1: iki aşamalı RRF, 1+2, 1+2+3 ve referans hibrit.
- **Tavan etkisi.** Bağlam düzeyinde varsayılan zaten 37/41. Kalan 4 sorudan (A07, A11, S06 ve
  koşuya göre A10 ya da S17) 3'ünü kurtarmadan kural sağlanamaz. Bu sorular çoğunlukla yanlış
  kavrama çevirme (A07, A11) ve benzer madde kalabalığı (S06). Ölçülen üç değişiklik bu nedenleri
  doğrudan hedeflemiyor.
- **İki aşamalı RRF arama düzeyinde daha görünür.** Bağlam düzeyinde +1 (dev1), arama düzeyinde +2
  (dev1 +1, dev2 +1). Teşhisteki A10 türü seyreltmeyi kısmen gideriyor, ama bağlam düzeyindeki farkı
  1. düzeltmenin (tablo eklemesi) zaten kapattığı ceza soruları küçültüyor.
- **Parça çeşitliliği tek başına etkisiz** (0). Çok parçalı maddelerin ceza sorularına etkisi bağlam
  düzeyinde 1. düzeltmeyle zaten giderilmişti.
- **Prompt v4 (özgün ifade kuralı) hafif zararlı** (dev2 −1). Hedeflediği A11'i kurtarmadı; A07'yi bir
  koşuda kaybettirdi. Belirli kavram eklemeden yapılan genel kural, kavram çevirme hatasını çözmüyor.
- **Referans bge-m3 hibrit (1+2)** de yalnız +1. A11'i ve S06'yı kurtarıp A07 ve S26'yı kaybediyor.
  Embedding bu sette BM25'in kaçırdığı kavramsal eşleşmeleri buluyor, ama net kazancı küçük.
- **Koşular arası oynama** (dev2 varsayılan: teşhiste 12/12/12, bu deneyde 13/12/13) değişikliklerin
  etkisiyle aynı büyüklükte. Bu da kuraldaki +3 eşiğinin neden gerekli olduğunu gösteriyor.

**Sonuç:** Arama varsayılanı olduğu gibi kalıyor ve `arama-donduruldu-2` etiketiyle yeniden
donduruluyor. Seçenek kodu (`birlestirme`, `max_parca_madde`, prompt v4) varsayılan dışı olarak duruyor.

