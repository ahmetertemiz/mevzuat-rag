# Yeniden yazım modeli karşılaştırması (BM25 + yeniden yazım)

`python scripts/compare_rewrite_models.py` tarafından üretilir. Geliştirme seti (`evals/retrieval.yaml`, 26 cevaplı soru). Holdout kullanılmadı.

- Prompt sürümü 2 (çok konulu sorularda konu başına en az bir sorgu, en fazla 4), effort `low`, JSON şeması; üç modelde aynı.
- Her model **3 kez, önbelleksiz** koşuldu; hücrelerde koşular arası aralık (en düşük–en yüksek).
- Sunucu tarafı reddetme fallback'i: claude-opus-5-5, claude-sonnet-5-5 (Haiku 5.5'te bu özellik yok).
- Çağrı hata verir ya da sorgu üretmezse soru düz BM25 ile aranır; "Hata" sütunu bunları sayar.
- Süre: tek çağrının uçtan uca süresi (istemci tarafı, 4 paralel istek). Maliyet: usage token'ları × liste fiyatı (Haiku 5.5 $0.10/$0.50, Sonnet 5.5 $2/$10, Opus 5.5 $4/$20 / 1M token).

## 1. Ana tablo

| Model | @1 | @3 | @5 | Madde dili @5 | Günlük dil @5 | İki madde @5 | Madde no @5 | Süre medyan / p95 | Maliyet / sorgu | Sorgu sayısı (ort.) | Hata |
|---|---|---|---|---|---|---|---|---|---|---|---|
| _düz BM25 (referans)_ | 11 | 15 | 18 | 6 | 3 | 4 | 5 | ~1 ms | $0 | 0 | — |
| `claude-haiku-5-5` | 14–17 | 19–21 | 22–23 | 6 | 7–8 | 4 | 5 | 1.3 / 1.7 sn | $0.00019 | 3.0 | 0 |
| `claude-sonnet-5-5` | 13–14 | 19–20 | 22–24 | 6 | 7–8 | 4–5 | 4–5 | 1.9 / 2.6 sn | $0.00392 | 3.6 | 0 |
| `claude-opus-5-5` | 14–17 | 20 | 22–23 | 6 | 8 | 4–5 | 4–5 | 1.8 / 2.8 sn | $0.00756 | 3.1 | 0 |

## 2. Soru türüne göre @1 / @3 / @5 (aralık)

| Model | Madde dili (n=7) | Günlük dil (n=8) | İki madde (n=6) | Madde numarası (n=5) |
|---|---|---|---|---|
| `claude-haiku-5-5` | 4–6 / 5–6 / 6 | 4–7 / 7–8 / 7–8 | 0 / 2–3 / 4 | 4–5 / 4–5 / 5 |
| `claude-sonnet-5-5` | 5 / 6 / 6 | 4–5 / 6 / 7–8 | 0 / 2–4 / 4–5 | 3–4 / 4–5 / 4–5 |
| `claude-opus-5-5` | 4–6 / 6 / 6 | 6–7 / 7 / 8 | 0 / 2–3 / 4–5 | 4–5 / 4–5 / 4–5 |

## 3. Kararsız sorular

@5 sonucu koşudan koşuya değişen sorular (✓ = ilk 5'te, ✗ = değil, koşu sırasıyla).

| Model | Sorular |
|---|---|
| `claude-haiku-5-5` | S09 (✓✗✓), S19 (✗✓✗), S20 (✓✗✓) |
| `claude-sonnet-5-5` | S14 (✓✗✓), S20 (✓✗✓), S26 (✗✓✓) |
| `claude-opus-5-5` | S19 (✗✗✓), S30 (✗✓✗) |

## 4. Her koşuda başarısız sorular (@5)

| Model | Sorular (doğru maddenin sırası, koşu sırasıyla) |
|---|---|
| `claude-haiku-5-5` | S06 (17, 10, 10), S16 (12/6, 7/8, 13/2) |
| `claude-sonnet-5-5` | S06 (15, 15, 12), S19 (7/2, 6/5, 6/5) |
| `claude-opus-5-5` | S06 (9, 10, 10), S20 (4/6, 6/3, 10/4) |

## 5. Örnek çıktılar (koşu 1, iki konulu sorular)

**S16** İnternetten aldığım ürün için cayma hakkımı kullandım. Ürünü kaç gün içinde geri göndermeliyim, satıcı da paramı kaç gün içinde iade etmeli?

- `claude-haiku-5-5`: `mesafeli sözleşmelerde cayma hakkının kullanılması süresi` · `cayma bedelinin iadesi süresi mesafeli satış` · `6502 sayılı Kanun mesafeli sözleşmeler cayma hakkı`
- `claude-sonnet-5-5`: `mesafeli sözleşmelerde cayma hakkı süresi` · `cayma hakkı kullanıldığında malın geri gönderilmesi süresi` · `cayma halinde satıcının bedel iade yükümlülüğü süresi` · `Mesafeli Sözleşmeler Yönetmeliği cayma hakkının kullanımı`
- `claude-opus-5-5`: `cayma hakkı kullanımında tüketicinin malı geri gönderme süresi` · `cayma bildiriminden itibaren malın satıcıya iadesi on gün` · `cayma hakkında satıcının bedeli iade süresi on dört gün` · `mesafeli sözleşmede cayma hakkı satıcının yükümlülükleri`

**S18** Tüketici hakem heyetine hangi tutarın altındaki uyuşmazlıklarda başvurulur, bu tutarın üstünde dava açmadan önce arabulucuya gitmek zorunlu mu?

- `claude-haiku-5-5`: `tüketici hakem heyeti parasal sınır başvuru değeri` · `tüketici uyuşmazlıklarında arabuluculuk dava şartı` · `6502 sayılı Kanun tüketici hakem heyeti görev sınırı`
- `claude-sonnet-5-5`: `tüketici hakem heyeti başvuru parasal sınır değer` · `tüketici hakem heyetine başvuru zorunluluğu uyuşmazlık değeri` · `tüketici uyuşmazlıklarında dava şartı arabuluculuk` · `tüketici mahkemesinde dava açmadan önce arabulucuya başvuru zorunluluğu`
- `claude-opus-5-5`: `tüketici hakem heyetine başvuru parasal sınırı` · `tüketici hakem heyeti görev alanı uyuşmazlık değeri` · `tüketici mahkemesinde dava açmadan önce zorunlu arabuluculuk` · `tüketici uyuşmazlıklarında arabulucuya başvurmanın dava şartı olması`

**S19** Kargoda kaybolan üründen kim sorumludur ve satıcı ürünü en geç kaç gün içinde teslim etmek zorundadır?

- `claude-haiku-5-5`: `mesafeli sözleşmelerde taşıma sırasında malın zarara uğraması sorumluluk` · `mesafeli sözleşmede satıcının malı teslim etme süresi` · `mesafeli sözleşmede teslimat süresi aşımı sözleşmeden dönme`
- `claude-sonnet-5-5`: `mesafeli sözleşmelerde malın teslimi ve taşıma sırasında kaybolma riski` · `satıcının malı teslim etme süresi otuz gün` · `teslimden önce mal kaybolması veya hasar görmesi satıcının sorumluluğu` · `satıcının ifa yükümlülüğünü yerine getirmemesi sözleşmeden dönme`
- `claude-opus-5-5`: `mal teslim edilinceye kadar kayıp ve hasardan satıcının sorumluluğu` · `taşıyıcıya teslim hasar riski mesafeli sözleşme` · `mesafeli sözleşmede malın teslim süresi otuz gün` · `satıcının ifa yükümlülüğü teslim süresi`

**S20** İnternet satışında satıcı sözleşme kurulmadan önce hangi bilgileri vermek zorundadır ve bu ön bilgilerin alındığı nasıl teyit edilir?

- `claude-haiku-5-5`: `mesafeli sözleşmelerde satıcının ön bilgilendirme yükümlülüğü` · `mesafeli sözleşmelerde ön bilgilerin tüketiciye teyit edilmesi` · `6502 sayılı Kanun mesafeli sözleşme ön bilgilendirme`
- `claude-sonnet-5-5`: `mesafeli sözleşmelerde ön bilgilendirme yükümlülüğü` · `mesafeli sözleşme ön bilgilendirme formu içeriği` · `ön bilgilendirmenin elektronik ortamda teyidi` · `tüketicinin ön bilgileri aldığını onaylaması`
- `claude-opus-5-5`: `mesafeli sözleşmelerde ön bilgilendirme yükümlülüğü` · `sözleşme kurulmadan önce tüketiciye verilecek bilgiler` · `ön bilgilerin alındığının teyidi` · `ön bilgilendirmenin ispat yükü satıcı`

**S21** Kişisel verilerimin silinmesini isteyebilir miyim ve bu talebimi veri sorumlusuna hangi yolla iletirim?

- `claude-haiku-5-5`: `kişisel verilerin silinmesi veya yok edilmesi talebi` · `veri sorumlusuna başvuru usul ve esasları` · `ilgili kişinin haklarına ilişkin veri sorumlusuna başvuru`
- `claude-sonnet-5-5`: `kişisel verilerin silinmesi veya yok edilmesi talebi ilgili kişinin hakları` · `6698 sayılı Kanun madde 11 ilgili kişinin hakları` · `veri sorumlusuna başvuru usulü yazılı başvuru` · `veri sorumlusunun başvuruyu sonuçlandırma süresi`
- `claude-opus-5-5`: `kişisel verilerin silinmesi yok edilmesi anonim hale getirilmesi` · `ilgili kişinin hakları kişisel verilerin silinmesini isteme` · `veri sorumlusuna başvuru usul ve esasları` · `ilgili kişinin veri sorumlusuna başvuru yolu yazılı başvuru`

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

