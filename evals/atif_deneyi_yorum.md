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
