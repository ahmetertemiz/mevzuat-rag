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
