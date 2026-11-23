# Atıf takibi deneyi

`python scripts/atif_deneyi.py` tarafından üretilir. Kural ölçümden önce `docs/kararlar.md`'ye kaydedildi. k=8, 3 koşu, yeniden yazım Haiku 5.5 (prompt v3); iki kol aynı aramayı paylaşır.

## 1. Bağlam düzeyi (kural a)

| Set | Kapalı (koşular) | Açık (koşular) | Medyan farkı |
|---|---|---|---|
| dev1 | 24 / 24 / 25 (medyan 24) | 25 / 24 / 25 (medyan 25) | +1 |
| dev2 | 13 / 12 / 12 (medyan 12) | 13 / 12 / 12 (medyan 12) | +0 |

**Toplam kazanç: +1** (eşik +2) → (a) sağlanmadı

### Değişen sorular (koşu sırasıyla; K = kapalı, A = açık)

| Set | Soru | Kapalı | Açık | Açıkta eklenen atıf parçaları (koşu 1) |
|---|---|---|---|---|
| dev1 | S15 | ✗✓✓ | ✓✓✓ | TKHK-m80-1 |

Atıf eki alan soru sayısı (koşu başına): dev1 [12, 6, 10]; dev2 [7, 5, 7]

## 2. Cevap değerlendirmesi (kural b; dev2, Haiku 5.5, 3 koşu)

| Ölçüt | Kapalı | Açık |
|---|---|---|
| Yanlış olgu (elle okuma; koşu başına) | — | — |
| Madde doğruluğu (cevaplı 15) | 9 / 10 / 11 | 9 / 10 / 11 |
| Yanlış reddetme (cevaplı 15) | 2 / 3 / 3 | 1 / 3 / 3 |
| Doğru reddetme (cevapsız 5) | 5 / 5 / 5 | 5 / 5 / 5 |
| Bağlamda (cevaplı 15) | 12 / 12 / 13 | 12 / 12 / 13 |
| Olgu oranı (%) | 62 / 71 / 71 | 71 / 71 / 75 |
| Çıkarılan cümle | 1 / 1 / 2 | 1 / 2 / 2 |

## 3. Karar

**Ret**: atıf takibi varsayılan olmaz (kod kapalı seçenek olarak kalır).

## 4. Yorum

- **Kural (a) sağlanmadı; atıf takibi reddedildi.** Toplam kazanç +1 (dev1 +1: S15, koşu 1'de m.80
  eklenince; dev2 0). Varsayılan değişmedi (`ATIF_TAKIBI_VARSAYILAN = False`); kod kapalı seçenek
  olarak duruyor.
- **(b) için elle okuma yapılmadı.** Kural iki koşulun birlikte sağlanmasını istiyor; (a) sağlanmadığı
  için sonuç (b)'den bağımsız olarak ret. Cevap koşuları `evals/atif_deneyi/` altında kayıtlı;
  otomatik ölçütlerde iki kol birbirine çok yakın (madde doğruluğu ikisinde de 9 / 10 / 11).
- **A15 çözülmedi, iki nedenle:**
  1. Cezayı m.47/2'ye bağlayan m.77/5 TKHK-m77-2 parçasında. Bu parça bazı koşularda aramanın ilk 3
     parçası arasında değil (bu deneyin koşu 1'inde ilk 3: m77-3, m77-7, ETK m12-5). Sınır gereği o
     koşuda atıfları izlenmedi.
  2. İlk 3'teki m.77 parçaları çok sayıda maddeye atıf yapıyor (m.53, 57/A, 58, 59, 47/A, 80 ...).
     En fazla 3 ek sınırı ve BM25 sıralaması m.47 yerine "satış" ve "yetki" kelimeleri geçen m.47/A
     (doğrudan satış), m.80 ve m.58'i seçti.
  Ayrıca A15'in setteki dayanağında m.47 olmadığı için bağlam ölçütü A15'teki bir kazanımı zaten
  gösteremezdi (bkz. evals/A15_teshis.md). Dayanak alanı değiştirilmedi.
- **Atıf eki sık devreye giriyor ama nadiren işe yarıyor.** Koşu başına dev1'de 6–12, dev2'de 5–7 soruya
  ek parça girdi; yalnız bir soruda (S15, bir koşu) bağlam sonucunu değiştirdi. Ceza maddeleri
  (m.77, ETK m.12) gibi atıf yoğun parçalar ilk sıralarda olduğunda ekler çoğunlukla soruyla ilgisiz.

