## 6. Yorum

Bu bölüm sonuçlara bakılarak elle yazıldı; hiçbir ayar değiştirilmedi.

**Üç modelin kalite aralıkları üst üste biniyor.** Haiku ve Opus'un aralıkları birebir aynı: @1 14–17, @5 22–23. Sonnet @1'de biraz geride (13–14), @5 aralığı daha geniş (22–24). 26 cevaplı soruda koşular arası oynama 2–3 soru. Bu oynama modeller arasındaki farktan büyük, yani bu setle aralarında kalite sıralaması yapılamaz.

**Maliyet ve süre belirgin biçimde ayrışıyor:**
- **Haiku:** $0.00019/sorgu, medyan 1,3 sn.
- **Sonnet:** $0.0039/sorgu, 1,9 sn. Haiku'nun yaklaşık 20 katı.
- **Opus:** $0.0076/sorgu, 1,8 sn. Haiku'nun yaklaşık 40 katı.
- **Ölçek:** 10.000 sorgu Haiku ile yaklaşık 2 $, Opus ile yaklaşık 76 $ tutar.

**Prompt v2'nin etkisi (S21):** İki konulu KVKK sorusunda "başvuru" gereksinimi (KVKK m.13) artık her modelde ve her koşuda 2. ya da 3. sırada. Prompt v1 ile yazımlı BM25'te 8. sıradaydı. Genel skorlarda ise v1'e göre ölçülebilir bir fark yok: Opus v1 tek koşuda @1/@3/@5 16/19/23, v2 üç koşuda 14–17 / 20 / 22–23.

**Modeller arasındaki nitel farklar:**
- **Haiku:** İki alt sorulu S16'yı her koşuda kaçırıyor. "Ürünü geri gönderme süresi" ile "paranın iade süresi"ni tek bir genel "cayma süresi" sorgusuna indiriyor ve geri gönderme maddesi (MSY m.13) bulunamıyor. Kural "her alt soru için en az bir sorgu" dediği hâlde ortalama 3,0 sorgu üretiyor.
- **Opus:** S16'yı (MSY m.13 her koşuda 1. sırada) ve madde numarası sorusu S26'yı (her koşuda 1.) en kararlı bulan model.
- **Sonnet:** Ortalama 3,6 sorguyla en çok sorgu üreten model. S21'de soruda olmayan bir madde numarası ekledi ("6698 sayılı Kanun madde 11"). Bu, prompt'taki "soruda olmayan madde numarası uydurma" kuralının ihlali; numara bu sefer doğru olsa da kural çiğnenmiş.
- **Bilgi sızması (Opus):** S16'nın bir sorgusuna "on gün" ifadesi girdi; doğrusu "on dört gün". Bu, yeniden yazımın soruyu cevaplamaya başladığını gösteriyor. Arama için zararı sınırlı (BM25 sayı kelimelerine ağırlık vermiyor), ama cevap üretiminde bu sorgular modele verilmemeli.

## 7. Öneri (model seçimi senin)

**Önerim: `claude-haiku-5-5`.** Gerekçeler:
- Bu sette kalite aralığı Opus'la aynı.
- Maliyeti yaklaşık 40 kat düşük, ve en hızlısı (medyan 1,3 sn).
- Yayın senaryosunda (ücretsiz barındırma, BM25 + yeniden yazım) her sorgu bir çağrı gerektirdiği için maliyet ve gecikme doğrudan kullanıcı deneyimine yansıyor.

Bilinen zayıflığı, iki alt sorulu sorularda konuları birleştirmesi (S16). Holdout'ta bu türden soru varsa Opus'a göre kayıp görülebilir.

**Kalite öncelikliyse alternatif: `claude-opus-5-5`.** İki konulu sorularda ve madde numarası sorgularında daha kararlı; bedeli 40 kat maliyet. Sonnet'i önermiyorum: maliyeti Haiku'nun 20 katı ve @1'de en düşük aralıkta.

Holdout tek yapılandırmayla, bir kez koşulacağı için seçilecek model holdout'tan önce sabitlenmeli. Koşular arası oynama yüzünden holdout'un kendisi de tek koşuda ±2–3 soru oynayabilir; bu, holdout sonucunu yorumlarken hesaba katılmalı.

## 8. Prompt v3: sayı kuralı ve sayı denetimi (Haiku 5.5, 3 koşu)

v3'te prompt'a "soruda geçmeyen sayı (süre, tutar, oran, tarih, kanun ve madde numarası) ekleme,
cevabı tahmin etme" kuralı eklendi. Kodda da bir denetim var: soruda olmayan bir sayı içeren sorgu
atılıyor ve sonuç nesnesinin `atilan_sorgular` alanında belirtiliyor.

| Haiku 5.5 | @1 | @3 | @5 | Günlük dil @1 / @5 | İki madde @5 | Atılan sorgu / koşu |
|---|---|---|---|---|---|---|
| prompt v2 (3 koşu) | 14–17 | 19–21 | 22–23 | 4–7 / 7–8 | 4 | (denetim yok) |
| prompt v3 (3 koşu) | 12–14 | 21 | 22–23 | 2–5 / 8 | 3–4 | 1 |

- **@3 ve @5 korunuyor.** @5 aralığı aynı. @3 en az v2'nin en iyisi kadar ve daha kararlı (3 koşuda da 21).
- **@1 düşüyor.** Düşüş 2–3 soru; v3'ün en iyi koşusu (14) v2'nin en kötüsüne (14) eşit. Bu yüzden kural @1'i hafifçe bozuyor. Nedeni ölçüldü:
  - v2'de Haiku 3 koşuda 67 sorguya sayı ya da süre eklemişti. Bunların bir kısmı doğru tahmindi.
  - Örnek S01: v2 sorgusu "cayma hakkı on dört gün" MSY m.9'un metniyle kelimesi kelimesine eşleşip onu 1. sıraya taşıyordu. v3'te bu sorgu yok ve madde 2.–3. sırada.
  - Kısacası v2'nin @1 avantajının bir bölümü, modelin cevabı doğru tahmin etmesinden geliyordu. Tahmin yanlış olduğunda (Opus'un "on gün" örneği) aynı mekanizma yanlış maddeyi öne çıkarabilir. v3 bu riski kaldırıyor, bedeli @1'de birkaç soru.
- **Modelin davranışı değişti.** Denetim 3 koşuda toplam yalnızca 3 sorgu attı; demek ki Haiku kurala büyük ölçüde uyuyor ve sayıları kendisi yazmıyor. Atılan 3 sorgunun hepsi S27'de ("KVKK 5. madde"): model KVKK'yı "6698 sayılı Kanun" olarak açmış, ama soruda "6698" geçmiyor. Bu bir cevap tahmini değil, doğru bir kısaltma açılımı. Katı kural bunu da atıyor; S27 yine de her koşuda bulundu (madde numarası soruları @5 5/5).
- **İki madde:** S19 v3'te her koşuda kaçıyor (teslim süresi gereksinimi 6.–7. sırada); v2'de de 3 koşudan 2'sinde kaçıyordu.
