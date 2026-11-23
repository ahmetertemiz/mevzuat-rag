# Yeniden yazım modeli karşılaştırması (BM25 + yeniden yazım)

`python scripts/compare_rewrite_models.py` tarafından üretilir. Geliştirme seti (`evals/retrieval.yaml`, 26 cevaplı soru). Holdout kullanılmadı.

- Prompt v2: çok konulu sorularda konu başına en az bir sorgu, en fazla 4. Prompt v3: ek olarak soruda geçmeyen sayı (süre, tutar, oran, tarih, kanun/madde numarası) yazma kuralı ve kodda sayı denetimi (böyle sorgular atılır). Effort `low`, JSON şeması; tüm satırlarda aynı.
- Her model **3 kez, önbelleksiz** koşuldu; hücrelerde koşular arası aralık (en düşük–en yüksek).
- Sunucu tarafı reddetme fallback'i: claude-opus-5-5, claude-sonnet-5-5 (Haiku 5.5'te bu özellik yok).
- Çağrı hata verir ya da sorgu üretmezse soru düz BM25 ile aranır; "Hata" sütunu bunları sayar.
- Süre: tek çağrının uçtan uca süresi (istemci tarafı, 4 paralel istek). Maliyet: usage token'ları × liste fiyatı (Haiku 5.5 $0.10/$0.50, Sonnet 5.5 $2/$10, Opus 5.5 $4/$20 / 1M token).

## 1. Ana tablo

| Model | @1 | @3 | @5 | Madde dili @5 | Günlük dil @5 | İki madde @5 | Madde no @5 | Süre medyan / p95 | Maliyet / sorgu | Sorgu sayısı (ort.) | Atılan sorgu / koşu | Hata |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| _düz BM25 (referans)_ | 11 | 15 | 18 | 6 | 3 | 4 | 5 | ~1 ms | $0 | 0 | — | — |
| `claude-haiku-5-5 · prompt v2` | 14–17 | 19–21 | 22–23 | 6 | 7–8 | 4 | 5 | 1.3 / 1.7 sn | $0.00019 | 3.0 | denetim yok | 0 |
| `claude-haiku-5-5 · prompt v3` | 12–14 | 21 | 22–23 | 6 | 8 | 3–4 | 5 | 1.3 / 2.0 sn | $0.00020 | 2.9 | 1 | 0 |
| `claude-sonnet-5-5 · prompt v2` | 13–14 | 19–20 | 22–24 | 6 | 7–8 | 4–5 | 4–5 | 1.9 / 2.6 sn | $0.00392 | 3.6 | denetim yok | 0 |
| `claude-opus-5-5 · prompt v2` | 14–17 | 20 | 22–23 | 6 | 8 | 4–5 | 4–5 | 1.8 / 2.8 sn | $0.00756 | 3.1 | denetim yok | 0 |

## 2. Soru türüne göre @1 / @3 / @5 (aralık)

| Model | Madde dili (n=7) | Günlük dil (n=8) | İki madde (n=6) | Madde numarası (n=5) |
|---|---|---|---|---|
| `claude-haiku-5-5 · prompt v2` | 4–6 / 5–6 / 6 | 4–7 / 7–8 / 7–8 | 0 / 2–3 / 4 | 4–5 / 4–5 / 5 |
| `claude-haiku-5-5 · prompt v3` | 4–5 / 6 / 6 | 2–5 / 7–8 / 8 | 0 / 2–3 / 3–4 | 4–5 / 5 / 5 |
| `claude-sonnet-5-5 · prompt v2` | 5 / 6 / 6 | 4–5 / 6 / 7–8 | 0 / 2–4 / 4–5 | 3–4 / 4–5 / 4–5 |
| `claude-opus-5-5 · prompt v2` | 4–6 / 6 / 6 | 6–7 / 7 / 8 | 0 / 2–3 / 4–5 | 4–5 / 4–5 / 4–5 |

## 3. Kararsız sorular

@5 sonucu koşudan koşuya değişen sorular (✓ = ilk 5'te, ✗ = değil, koşu sırasıyla).

| Model | Sorular |
|---|---|
| `claude-haiku-5-5 · prompt v2` | S09 (✓✗✓), S19 (✗✓✗), S20 (✓✗✓) |
| `claude-haiku-5-5 · prompt v3` | S20 (✗✓✗) |
| `claude-sonnet-5-5 · prompt v2` | S14 (✓✗✓), S20 (✓✗✓), S26 (✗✓✓) |
| `claude-opus-5-5 · prompt v2` | S19 (✗✗✓), S30 (✗✓✗) |

## 4. Her koşuda başarısız sorular (@5)

| Model | Sorular (doğru maddenin sırası, koşu sırasıyla) |
|---|---|
| `claude-haiku-5-5 · prompt v2` | S06 (17, 10, 10), S16 (12/6, 7/8, 13/2) |
| `claude-haiku-5-5 · prompt v3` | S06 (17, 10, 18), S16 (9/3, 8/3, 8/3), S19 (3/6, 4/7, 3/6) |
| `claude-sonnet-5-5 · prompt v2` | S06 (15, 15, 12), S19 (7/2, 6/5, 6/5) |
| `claude-opus-5-5 · prompt v2` | S06 (9, 10, 10), S20 (4/6, 6/3, 10/4) |

## 5. Örnek çıktılar (koşu 1, iki konulu sorular)

**S16** İnternetten aldığım ürün için cayma hakkımı kullandım. Ürünü kaç gün içinde geri göndermeliyim, satıcı da paramı kaç gün içinde iade etmeli?

- `claude-haiku-5-5 · prompt v2`: `mesafeli sözleşmelerde cayma hakkının kullanılması süresi` · `cayma bedelinin iadesi süresi mesafeli satış` · `6502 sayılı Kanun mesafeli sözleşmeler cayma hakkı`
- `claude-haiku-5-5 · prompt v3`: `mesafeli sözleşmelerde cayma hakkı kullanım süresi` · `cayma hakkında ürünün iadesi ve satıcının bedeli iade etme süresi` · `mesafeli satışta cayma bildiriminin ardından bedelin iadesi`
- `claude-sonnet-5-5 · prompt v2`: `mesafeli sözleşmelerde cayma hakkı süresi` · `cayma hakkı kullanıldığında malın geri gönderilmesi süresi` · `cayma halinde satıcının bedel iade yükümlülüğü süresi` · `Mesafeli Sözleşmeler Yönetmeliği cayma hakkının kullanımı`
- `claude-opus-5-5 · prompt v2`: `cayma hakkı kullanımında tüketicinin malı geri gönderme süresi` · `cayma bildiriminden itibaren malın satıcıya iadesi on gün` · `cayma hakkında satıcının bedeli iade süresi on dört gün` · `mesafeli sözleşmede cayma hakkı satıcının yükümlülükleri`

**S19** Kargoda kaybolan üründen kim sorumludur ve satıcı ürünü en geç kaç gün içinde teslim etmek zorundadır?

- `claude-haiku-5-5 · prompt v2`: `mesafeli sözleşmelerde taşıma sırasında malın zarara uğraması sorumluluk` · `mesafeli sözleşmede satıcının malı teslim etme süresi` · `mesafeli sözleşmede teslimat süresi aşımı sözleşmeden dönme`
- `claude-haiku-5-5 · prompt v3`: `mesafeli sözleşmelerde taşıma sırasında malın zararından satıcının sorumluluğu` · `mesafeli sözleşmelerde malın teslim süresi` · `mesafeli sözleşmede malın tüketiciye teslimi ve teslim yükümlülüğü`
- `claude-sonnet-5-5 · prompt v2`: `mesafeli sözleşmelerde malın teslimi ve taşıma sırasında kaybolma riski` · `satıcının malı teslim etme süresi otuz gün` · `teslimden önce mal kaybolması veya hasar görmesi satıcının sorumluluğu` · `satıcının ifa yükümlülüğünü yerine getirmemesi sözleşmeden dönme`
- `claude-opus-5-5 · prompt v2`: `mal teslim edilinceye kadar kayıp ve hasardan satıcının sorumluluğu` · `taşıyıcıya teslim hasar riski mesafeli sözleşme` · `mesafeli sözleşmede malın teslim süresi otuz gün` · `satıcının ifa yükümlülüğü teslim süresi`

**S21** Kişisel verilerimin silinmesini isteyebilir miyim ve bu talebimi veri sorumlusuna hangi yolla iletirim?

- `claude-haiku-5-5 · prompt v2`: `kişisel verilerin silinmesi veya yok edilmesi talebi` · `veri sorumlusuna başvuru usul ve esasları` · `ilgili kişinin haklarına ilişkin veri sorumlusuna başvuru`
- `claude-haiku-5-5 · prompt v3`: `kişisel verilerin silinmesi talebi` · `veri sorumlusuna başvuru usulü ve yöntemi` · `ilgili kişinin kişisel verilere ilişkin hakları`
- `claude-sonnet-5-5 · prompt v2`: `kişisel verilerin silinmesi veya yok edilmesi talebi ilgili kişinin hakları` · `6698 sayılı Kanun madde 11 ilgili kişinin hakları` · `veri sorumlusuna başvuru usulü yazılı başvuru` · `veri sorumlusunun başvuruyu sonuçlandırma süresi`
- `claude-opus-5-5 · prompt v2`: `kişisel verilerin silinmesi yok edilmesi anonim hale getirilmesi` · `ilgili kişinin hakları kişisel verilerin silinmesini isteme` · `veri sorumlusuna başvuru usul ve esasları` · `ilgili kişinin veri sorumlusuna başvuru yolu yazılı başvuru`

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

