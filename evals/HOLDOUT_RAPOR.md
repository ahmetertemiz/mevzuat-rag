# Holdout raporu

Sistem `sistem-donduruldu-holdout` etiketinde donduruldu ve holdout (`evals/holdout.yaml`, 20 soru: 17 cevaplı, 3 cevapsız) **bir kez** koşuldu: `python scripts/holdout.py`. Hat: BM25 + yeniden yazım (Haiku 5.5, prompt v3), k=8, atıf takibi kapalı; cevap Haiku 5.5. Holdout sonuçlarına göre hiçbir şey değiştirilmedi.

**Setin kaynağı:** Sorular proje sahibi yerine sohbetteki Claude tarafından yazıldı; yazan geliştirme setlerini görmüştü (sınır `evals/holdout.yaml` başında). Bu nedenle holdout tam bağımsız değil.

Hücreler: en düşük / medyan / en yüksek (3 koşu). Yüzdeler medyandan.

## 1. Arama

| Ölçüt | dev1 (26) | dev2 (15) | **holdout (17)** |
|---|---|---|---|
| @1 | 15 / 15 / 17 (%58) | — | **7 / 8 / 10 (%47)** |
| @3 | 19 / 22 / 22 (%85) | — | **10 / 11 / 12 (%65)** |
| @5 | 23 / 23 / 24 (%88) | — | **12 / 13 / 13 (%76)** |
| Bağlam düzeyi, k=8 | 24 / 24 / 25 (%92) | 12 / 12 / 13 (%80) | **12 / 13 / 14 (%76)** |

dev1 @k: `evals/RAPOR_retrieval_varsayilan.md`; bağlam düzeyi: aynı sistemin son ölçümü (`evals/ATIF_DENEYI.md`, takipsiz kol). dev2 için @1/@3/@5 ölçülmedi (dayanak alanı bağlam düzeyinde kullanılır).

### Türe göre (holdout)

| Tür | n | @1 | @3 | @5 | Bağlam k=8 |
|---|---|---|---|---|---|
| madde_dili | 1 | 0 / 1 / 1 | 1 / 1 / 1 | 1 / 1 / 1 | 1 / 1 / 1 |
| gunluk_dil | 14 | 6 / 8 / 9 | 9 / 10 / 11 | 10 / 11 / 11 | 10 / 11 / 12 |
| iki_madde | 2 | 0 / 0 / 0 | 0 / 0 / 0 | 1 / 1 / 1 | 1 / 1 / 1 |

### Soru bazında (koşu sırasıyla)

| Soru | Tür | Doğru maddenin sırası | @5 | Bağlam k=8 |
|---|---|---|---|---|
| H01 | gunluk_dil | 1, 1, 4 | ✓✓✓ | ✓✓✓ |
| H02 | gunluk_dil | 7, 12, 4 | ✗✗✓ | ✓✗✓ |
| H03 | gunluk_dil | 1, 1, 1 | ✓✓✓ | ✓✓✓ |
| H04 | gunluk_dil | 1, 1, 1 | ✓✓✓ | ✓✓✓ |
| H05 | gunluk_dil | 2, 2, 2 | ✓✓✓ | ✓✓✓ |
| H06 | gunluk_dil | 1, 1, 2 | ✓✓✓ | ✓✓✓ |
| H07 | gunluk_dil | 1, 1, 1 | ✓✓✓ | ✓✓✓ |
| H08 | gunluk_dil | 2, 2, 2 | ✓✓✓ | ✓✓✓ |
| H09 | gunluk_dil | 1, 1, 1 | ✓✓✓ | ✓✓✓ |
| H10 | gunluk_dil | 11, 15, 47 | ✗✗✗ | ✗✗✗ |
| H11 | gunluk_dil | 1, 1, 1 | ✓✓✓ | ✓✓✓ |
| H12 | gunluk_dil | 1, 17, 22 | ✓✗✗ | ✓✗✗ |
| H13 | gunluk_dil | 25, 11, 22 | ✗✗✗ | ✗✗✗ |
| H14 | gunluk_dil | 1, 1, 1 | ✓✓✓ | ✓✓✓ |
| H15 | iki_madde | 1/16, 2/24, 5/23 | ✗✗✗ | ✗✗✗ |
| H16 | iki_madde | 5/2, 5/2, 5/2 | ✓✓✓ | ✓✓✓ |
| H17 | madde_dili | 1, 2, 1 | ✓✓✓ | ✓✓✓ |

## 2. Cevap (otomatik ölçütler; elle okuma ayrıca yapılacak)

Holdout: tek koşu, 1. arama koşusunun bağlamıyla. dev2: aynı sistem, 3 koşu (`evals/atif_deneyi/cevap_kapali_kosu*.json`).

| Ölçüt | dev2 (15 cevaplı + 5 cevapsız) | **holdout (17 + 3)** |
|---|---|---|
| Cevaplandı | 8 / 9 / 9 | **10** |
| Kısmen cevaplandı | 3 / 4 / 4 | **7** |
| Bulunamadı (cevaplı soruda) | 2 / 3 / 3 | **0** |
| Alıntı doğrulama oranı (%) | 94.9 / 97.5 / 97.6 | **98.0** (49 alıntı) |
| Çıkarılan cümle | 1 / 1 / 2 | **1** / 46 cümle (1 cevapta) |
| Cevapsız soruda reddetme | 5 / 5 / 5 (5 soruda) | **3 / 3** |
| Sistem hatası (okunamayan çıktı) | 0 / 0 / 0 | **0** |

### Soru bazında durum (holdout)

| Soru | Tür | Durum | Gösterilen / çıkarılan cümle | Uyarılar |
|---|---|---|---|---|
| H01 | gunluk_dil | kismen_cevaplandi | 2 / 0 | — |
| H02 | gunluk_dil | cevaplandi | 2 / 0 | — |
| H03 | gunluk_dil | cevaplandi | 3 / 0 | — |
| H04 | gunluk_dil | cevaplandi | 3 / 0 | — |
| H05 | gunluk_dil | cevaplandi | 3 / 0 | — |
| H06 | gunluk_dil | kismen_cevaplandi | 2 / 1 | model:ceza_tutari_belirsiz |
| H07 | gunluk_dil | cevaplandi | 3 / 0 | — |
| H08 | gunluk_dil | cevaplandi | 2 / 0 | — |
| H09 | gunluk_dil | cevaplandi | 2 / 0 | — |
| H10 | gunluk_dil | kismen_cevaplandi | 4 / 0 | — |
| H11 | gunluk_dil | cevaplandi | 1 / 0 | — |
| H12 | gunluk_dil | kismen_cevaplandi | 2 / 0 | — |
| H13 | gunluk_dil | kismen_cevaplandi | 3 / 0 | — |
| H14 | gunluk_dil | kismen_cevaplandi | 4 / 0 | — |
| H15 | iki_madde | kismen_cevaplandi | 3 / 0 | — |
| H16 | iki_madde | cevaplandi | 4 / 0 | — |
| H17 | madde_dili | cevaplandi | 2 / 0 | — |
| H18 | cevapsiz | bulunamadi | 0 / 0 | — |
| H19 | cevapsiz | bulunamadi | 0 / 0 | — |
| H20 | cevapsiz | bulunamadi | 0 / 0 | — |

## 3. Otomatik gözlemler (cevaplar elle değerlendirilmedi)

- **Arama holdout'ta dev1'den belirgin biçimde zayıf, dev2'ye yakın.** Bağlam düzeyinde holdout %76
  (12–14 / 17), dev2 %80, dev1 %92. @5'te holdout %76, dev1 %88. Arama seçeneklerinin seçildiği dev1
  iyimser çıktı; README'deki "iki set arasındaki fark" holdout'ta dev2 tarafında doğrulandı.
- **Her koşuda kaçan sorular:** H10 (KVKK m.8, aktarım), H13 (MSY m.15, kişiye özel mal), H15'in
  ikinci gereksinimi (TKHK m.45, dönme hakkı). H12 (MSY m.19) ve H02 (TKHK m.58) koşuya göre değişiyor.
- **Cevapsız 3 soru** reddedildi (3/3); okunamayan çıktı yok; alıntı doğrulama %98, 46 cümleden 1'i
  çıkarıldı.
- **Holdout'ta cevaplı hiçbir soruda "bulunamadı" yok** (dev2'de 2–3). Beklenen madde bağlamda
  değilken (1. koşu: H10, H13, H15) model "kısmen cevaplandı" verdi ve başka maddelere dayandı:
  H10 KVKK m.3, 5, 11; H13 MSY m.12 ve TKHK m.48; H15 TKHK m.43 ve MSY m.10. Bu cevapların doğru
  ya da yanıltıcı olduğu elle okumada belirlenecek; burada değerlendirilmedi.
- Holdout sonuçlarına göre hiçbir ayar değiştirilmedi.

## 4. Elle okuma

20 cevabın hepsi sohbetteki Claude tarafından elle okundu (2026-11-23). Bu bölüm o okumanın bulgularını
aktarır; sistem kodu, prompt'lar ve holdout dosyası bu bulgulara göre değiştirilmedi.

| Ölçüt | Sonuç |
|---|---|
| Beklenen bilgi doğru verildi (cevaplı 17) | **14 / 17** |
| Yanlış sayı, süre ya da tutar | **0** |
| Cevapsız soruda reddetme | **3 / 3** |
| Yanlış rejimin hükmünü uygulama | 1 (H07) |
| Somut olaya yorum | 1 (H09) |

Soru bazında bulgular:

- **H07 – yanlış rejim.** Devre tatil sorusuna Mesafeli Sözleşmeler Yönetmeliği m.10 hükmü
  (bilgilendirilmeyen tüketicinin on dört günlük süreyle bağlı olmaması) uygulandı. Alıntı MSY
  m.10'da birebir geçtiği için doğrulamadan geçti. Mevcut denetimler (alıntı, sayı, uyarı dayanağı)
  bu hata türünü yakalamıyor: alıntı doğru, ama madde sorunun konusuna ait değil.
- **H09 – somut olaya yorum.** Cevap, kullanıcının durumunun istisna kapsamında
  "değerlendirilebileceğini" söyleyerek somut olaya yorum yaptı (prompt kural 4'e aykırı). Ayrıca
  holdout notu KVKK m.28/1(a)'daki "aynı konutta yaşayan" kaydını atlamıştı; bu, soru yazarının hatası.
- **H13 – istisna bağlama gelmedi.** İstisna maddesi (MSY m.15/1-b, kişiye özel hazırlanan mallar)
  bağlamda yoktu. Cevap genel cayma kuralını verdi; istisnanın bulunamadığını yalnız altta ("bulunamayan")
  belirtti. Cümleler tek tek doğru, ama bütün olarak okuyanı "iade edebilirim" sonucuna götürebilir.
- **H10, H15 – madde bağlamda yok, eksik açıkça belirtildi.** Beklenen madde (KVKK m.8; TKHK m.45)
  bağlamda değildi; model eksik kısmı açıkça yazdı.

