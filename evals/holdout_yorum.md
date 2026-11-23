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
