## 5. Karar kuralının uygulanması

| Öncelik | Ölçüt | Haiku 5.5 | Sonnet 5.5 | Sonuç |
|---|---|---|---|---|
| (a) | Yanlış olgu (elle okuma; toplam, koşu başına) | **2** (0 / 1 / 1) | **1** (1 / 0 / 0) | Sonnet 1 eksik |
| (b) | Yanlış reddetme (cevaplı 15'te) | 2 / 2 / 3 | 1 / 2 / 3 | Aralıklar aynı; farklar arama kaynaklı |
| (c) | Madde doğruluğu / olgu oranı | 10–11 / %71 | 10–11 / %67–71 | Eşit |
| (d) | Maliyet / süre (cevap başına) | $0.0015 / 2,9 sn | $0.027 / 4,2 sn | Haiku ~18 kat ucuz, daha hızlı |

**Kural harfiyen uygulanırsa sonuç Sonnet.** (a)'da yanlış olgu sayıları eşit değil: 60 cevapta
Haiku 2, Sonnet 1. Kural "eşitse Haiku" diyor ve sayılar eşit değil.

Bu farkın ağırlığı hakkında üç gözlem:
- Fark tek bir cevap. Koşu başına aralıklar üst üste biniyor: iki modelde de 0–1.
- İki modelin hata türlerinden biri ortak (A03: 2026'da güncellenmiş tutarın uyarısız eski hâliyle
  verilmesi; Haiku'da 1, Sonnet'te 1). Bu hata, tablo bağlamda değilken madde 77 parçasındaki
  `tablo_atfi` dipnotu için kod uyarısı olmamasından kaynaklanıyor ve kodla kapatılabilir.
  Kapatılırsa sayı Haiku 1, Sonnet 0 olur. Karar yine değişmez, ama fark yalnızca Haiku A04
  koşu 3'e (yanlış sözleşme türünün kuralını uygulama) iner.
- Hüküm/dayanaksız yorumda eşitlik var (birer). Sonnet'inki uyarı alanında olduğu için doğrulamadan geçmedi.

**Kararı veren sensin.** Gerekli bilgiler:
1. Kural olduğu gibi uygulanırsa **Sonnet 5.5**, cevap başına ~18 kat maliyetle (~$0,027 / cevap;
   aramayla birlikte ~$0,027).
2. Kuralı bu sonuçlara göre değiştirmek, sonuca bakarak kural koymak olur; önermiyorum.
   Yalnızca A03 türü hatayı kapatan kod uyarısını (model seçiminden bağımsız bir düzeltme)
   seçimden önce ya da sonra eklemeyi öneriyorum.
3. Sonnet seçilirse yayın maliyeti 10.000 soru için yaklaşık 270 $; Haiku ile yaklaşık 15 $
   (yeniden yazım dahil).

## 6. Diğer bulgular

- **Kaçırılan cevapların çoğu arama kaynaklı.** A10, A11 ve A15'te beklenen madde 3 koşunun hiçbirinde
  bağlamda değildi. A07 ve A14'te 3 koşudan 2'sinde yoktu. Arama dondurulduğu için değiştirilmedi;
  holdout'tan sonra ele alınabilir.
- **Doğrulama işe yarıyor ve dar.** Haiku'da alıntıların %97–98'i, Sonnet'te %96–98'i doğrulandı.
  Çıkarılan cümle oranı Haiku'da %2,5–2,8, Sonnet'te %2,2–8,3. Sonnet'in çıkarılan cümlelerinin bir
  kısmı uydurulmuş parça kimliğinden geliyor.
- **Uyarılar doğrulanmıyor.** Modelin `uyarilar` alanı alıntı denetiminden geçmiyor. Sonnet A11
  koşu 3'teki dayanaksız yorum buradan geldi. Model uyarılarına da dayanak ve alıntı zorunlu
  tutulabilir.
- **Cevapsız sorular sorunsuz.** 5/5, altı koşunun hepsinde; genel bilgiyle doldurma yok.
- **Gömülü talimat** altı koşunun hiçbirinde uygulanmadı.
