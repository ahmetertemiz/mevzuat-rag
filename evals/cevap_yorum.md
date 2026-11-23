## 5. Karar kuralının uygulanması

| Öncelik | Ölçüt | Haiku 5.5 | Sonnet 5.5 | Sonuç |
|---|---|---|---|---|
| (a) | Yanlış olgu (elle okuma; 3 koşu toplamı, koşu başına) | **0** (0 / 0 / 0) | **0** (0 / 0 / 0) | Fark 0 |
| (b) | Yanlış reddetme (cevaplı 15'te) | 2 / 3 / 3 | 1 / 2 / 2 | Sonnet 1 iyi |
| (c) | Madde doğruluğu / olgu oranı | 9–11 / %58–75 | 10–12 / %67–71 | Sonnet biraz iyi |
| (d) | Maliyet / süre (cevap başına) | $0,0017 / 2,6 sn | $0,030 / 4,2 sn | Haiku ~18 kat ucuz, daha hızlı |

**Gürültü payı kuralı:** Sonnet ancak 3 koşunun toplamında yanlış olgu sayısı Haiku'dan en az 2 daha
azsa seçilir. Toplamlar 0 ve 0; fark 0 < 2. **Sonuç: Haiku 5.5** (`CEVAP_MODEL` değişmez).

(b) ve (c)'deki Sonnet üstünlüğü kural gereği seçimi değiştirmiyor: gürültü payı kuralı (a)'yı
eşik yapıyor, eşik geçilmeyince Haiku kalıyor. Bu farklar bilgi olarak kayda geçiyor.

## 6. Önceki ölçümle (v1) karşılaştırma

| | v1 Haiku | v1 Sonnet | v2 Haiku | v2 Sonnet |
|---|---|---|---|---|
| Yanlış olgu (toplam) | 2 | 1 | 0 | 0 |
| Hüküm / dayanaksız yorum | 1 | 1 | 0 | 0 |
| Uyarı isabeti (medyan, 3'te) | 3 | 3 | 1 | 2 |

- **Yanlış olguların ikisi de kod düzeltmeleriyle kapandı.** A03 türü hata (güncellenmiş tutarın
  uyarısız eski hâli) artık her koşuda `tutar_guncellenir` uyarısıyla geliyor. A04 türü hata
  (başka sözleşme türünün kuralı) bu ölçümde tekrarlanmadı. Bu ikincisi kodla değil, koşu
  değişkenliğiyle açıklanabilir; tek örnekten kapandığı söylenemez.
- **Dayanaksız model uyarısı kapandı.** Uyarılara dayanak zorunluluğu (kural 8) sonrası Sonnet'in bir
  uyarısı (A03 k1) doğrulanamadığı için çıkarıldı; gösterilen model uyarılarının hepsi doğru çıktı.
- **Uyarı isabeti iki modelde de düştü (Haiku 3 → 1, Sonnet 3 → 2).** Nedenleri üretim tarafında:
  - A15 (iki model, altı koşu): v1'de isabet, modelin dayanaksız `ceza_tutari_belirsiz` uyarısından
    geliyordu (cevap yine "bulunamadi"ydı). 3. kod düzeltmesi uyarılara dayanak zorunluluğu getirdi;
    model artık bu uyarıyı hiç üretmiyor (çıkarılan uyarı da yok). Yani v1'deki isabetin bir kısmı
    doğrulanmamış bir uyarıdan geliyordu; düşüş kısmen ölçümün dürüstleşmesi.
  - A13 Haiku koşu 3: model çıktısı ayrıştırılamadı ("Model çıktısı okunamadı"), cevap ve `aym_iptal`
    uyarısı gösterilmedi.
  - A12 Haiku koşu 1: iki cümle de alıntısı birebir olmadığı için çıkarıldı, cevap "bulunamadi"ya
    düştü. Kod uyarıları yalnız doğrulanmış dayanak parçalarından üretildiği için `mulga` uyarısı da
    kayboldu (mülga madde bağlamda olduğu hâlde). Bağlamdaki mülga parçalar için dayanaktan bağımsız
    uyarı üretmek bunu kapatır (uygulanmadı; cevap üretimi bu ölçümde değiştirilmedi).
- **A15'te tablo artık bağlamda, ama iki model de cevap vermiyor.** 1. kod düzeltmesi (tablo
  eklemesi) arama tarafındaki eksikliği kapattı (bağlam sütunu ✓✓✓). Kalan sorun üretimde: iki model
  de altı koşunun hepsinde tablodaki tutarı (ve yetkisiz kapıdan satışın hangi fıkraya girdiğini)
  bağlamaktan kaçınıyor. Nedenini bu ölçüm göstermiyor (bağlamın tam okunması gerekir); sonuç yanlış
  olgu üretmiyor, yanlış reddetme olarak sayılıyor.

## 7. Diğer bulgular

- **Kalan kaçırmaların bir kısmı arama kaynaklı.** A10 ve A11'de beklenen madde 3 koşunun hiçbirinde
  bağlamda değildi (A07 koşu 1'de yoktu). Arama dondurulduğu için değiştirilmedi.
- **Haiku'da doğrulayıcı daha çok çalışıyor.** Çıkarılan cümle oranı Haiku'da %2,6–7,5, Sonnet'te
  %0–2,2. Haiku'nun çıkarılan cümleleri alıntının birebir olmamasından geliyor (özellikle mülga
  madde A12). Bunlar gösterilmediği için yanlış olgu üretmiyor, ama cevabı kısaltıyor ya da
  boşaltıyor.
- **Cevapsız sorular sorunsuz** (5/5, altı koşuda). **Gömülü talimat** hiçbir koşuda uygulanmadı.
