## 7. Yorum

Bu bölüm sonuçlara bakılarak elle yazıldı. Hiçbir ayar değiştirilmedi; varsayılan hâlâ `bge-m3 hibrit`.

**Yeniden yazım her yapılandırmada @1'i artırıyor.** Artış +4 ile +7 soru arasında. @5'te de bir yapılandırma dışında artış var; istisna yalnız bge-m3 embedding (23 → 22). En büyük kazanç BM25'te: @5 18 → 23, günlük dil 3/8 → 8/8. BM25'in yapısal zayıflığı olan kelime uyuşmazlığını (`kargo` / `taşıyıcı`, `kampanya mesajı` / `ticari elektronik ileti`) model çağrısı kapatıyor. Bedeli soru başına bir model çağrısı: ortalama $0.0064 (`claude-opus-5-5`, effort `low`) ve medyan yaklaşık 2 saniye ek gecikme. Bu, aramanın kendisinden 10 ile 100 kat daha uzun.

**Yeniden yazımın tutarlı iki kaybı var:**
- **S21 (iki konulu soru):** Üretilen üç sorgudan ikisi "silme" konusunu, biri "başvuru" konusunu hedefliyor. RRF çok listede geçen maddeyi öne aldığı için KVKK m.13 geriye düşüyor. Bu kayıp 9 yazımlı yapılandırmanın 8'inde görülüyor.
- **S26 (madde numarası):** Üretilen sorgular madde numarasını koruyor ve BM25 doğru maddeyi buluyor. Ama aynı sorgular embedding'e de giriyor; embedding numarayı anlamsal olarak çözemediği için ürettiği sıralamalar gürültü ekliyor. bge-m3 ve Granite hibritlerinde birleşim doğru maddeyi 1. sıradan 6.–9. sıraya itiyor. Yazımlı BM25'te bu kayıp yok.

**Küçük embedding modelleri bu sette belleklerini hak etmiyor:**
- **Granite-97M:** Yazımsız hâlde bge-m3'ün belirgin gerisinde (@5 hibrit 19'a karşı 22). En zayıf olduğu tür madde numarası soruları (embedding 0/5). Float32 ile bfloat16 arasında kalite farkı yok. Float32 sürümü bu işlemcide yaklaşık 2,5 kat daha hızlı (16 ms'ye karşı 40 ms), sorgu sırasında 823 MB kullanıyor.
- **e5-small:** 512 token sınırı yüzünden 34 parça kesiliyor. Ölçülen bellek 1.179 MB, yani 1 GB hedefinin üstünde.
- **Karşılaştırma:** İki küçük model de yazımla birlikte bile yazımlı BM25'i geçemiyor. Yazımlı BM25 aynı @5'i (23/26) torch yüklemeden, yaklaşık 40 MB ile veriyor.

**Farklar küçük.** Cevaplı 26 soruda bir soru yaklaşık 4 puan. En iyi üç yapılandırma arasındaki fark @5'te 1 soru, @1'de 1–2 soru. Bu fark tek başına bir sıralama kurmaya yetmez; seçilen yöntem holdout setinde doğrulanmalı.

## 8. Öneri (uygulanmadı)

Kararı barındırma ortamının belleği belirliyor. İki aday var:

| | A: `bge-m3 hibrit + yeniden yazım` | B: `BM25 + yeniden yazım` |
|---|---|---|
| @1 / @3 / @5 (26) | 17 / 22 / 24 | 16 / 19 / 23 |
| Bellek (sorgu tepe) | ~1,9 GB (+ torch) | ~40 MB, torch gerekmez |
| Sorgu süresi | ~250 ms + ~2 sn çağrı | ~1 ms + ~2 sn çağrı |
| Maliyet / sorgu | $0.0064 | $0.0064 |
| Model API'si çalışmazsa | bge-m3 hibrit'e düşer (@5 22/26) | düz BM25'e düşer (@5 18/26, günlük dil 3/8) |

**Önerim: B (`BM25 + yeniden yazım`).** Gerekçem, ücretsiz barındırma hedefi. B, bu sette A'dan yalnızca 1 soru geride; bellek ihtiyacı ise yaklaşık 50 kat küçük. Torch ve embedding modeli kurulumunu, yaklaşık 9 saniyelik soğuk başlangıcı ve 4 GB'lık model önbelleğini de ortadan kaldırıyor. B'nin zayıf yanları:
- API'ye tam bağımlı. Çağrı başarısız olursa kalite belirgin biçimde düşer.
- Gecikmenin neredeyse tamamı model çağrısından geliyor.

Holdout öncesinde senin karar vermen gereken noktalar:

1. **Yeniden yazım modeli.** Ölçüm `claude-opus-5-5` ile yapıldı; varsayılan model bu. Daha ucuz bir modele (ör. `claude-haiku-5-5`) geçmek maliyeti ve gecikmeyi düşürebilir, ama bu ölçülmedi. Geçilecekse önce bu geliştirme setinde ölçülmeli.
2. **S21 ve S26 kayıpları için olası düzeltmeler.** Örnekler: madde numarası içeren sorgularda yalnız BM25 kullanmak ya da özgün sorguya daha yüksek ağırlık vermek. Bunlar bu sete göre ayar yapmak olur; yapılacaksa holdout'tan önce yapılmalı ve holdout bir kez koşulmalı.
3. **Holdout'ta neyin koşulacağı.** Yalnızca seçilen yapılandırma mı, yoksa A ve B birlikte mi? İkisini birlikte koşmak holdout üzerinde seçim yapmak anlamına gelir; öneri tek yapılandırma.
