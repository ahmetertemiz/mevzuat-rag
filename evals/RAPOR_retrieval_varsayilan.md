# Varsayılan hat değerlendirmesi: retrieval

`python scripts/eval_retrieval.py --set evals/retrieval.yaml --varsayilan --runs 3` ile üretildi. Hat: `bm25` + yeniden yazım (`claude-haiku-5-5`, prompt v3), önbelleksiz, **3 koşu**. Cevaplı soru: 26.

## Özet (en düşük / medyan / en yüksek)

| | @1 | @3 | @5 |
|---|---|---|---|
| Cevaplı 26 soru | 15 / 15 / 17 | 19 / 22 / 22 | 23 / 23 / 24 |
| Madde dili (n=7) | 4 / 5 / 5 | 6 / 6 / 6 | 6 / 6 / 6 |
| Günlük dil (n=8) | 6 / 7 / 7 | 8 / 8 / 8 | 8 / 8 / 8 |
| İki madde (n=6) | 0 / 0 / 0 | 1 / 3 / 3 | 4 / 4 / 5 |
| Madde numarası (n=5) | 4 / 4 / 5 | 4 / 5 / 5 | 5 / 5 / 5 |

## Koşular

| Koşu | @1 | @3 | @5 | Başarısız yazım | Atılan sorgu | Maliyet | Yazım süresi medyanı |
|---|---|---|---|---|---|---|---|
| 1 | 15 | 22 | 24 | 0 | 0 | $0.0061 | 1.4 sn |
| 2 | 17 | 22 | 23 | 0 | 0 | $0.0060 | 1.3 sn |
| 3 | 15 | 19 | 23 | 0 | 0 | $0.0062 | 1.2 sn |

## Soru bazında doğru maddenin sırası (koşu sırasıyla)

| Soru | Tür | Sıralar | @5 |
|---|---|---|---|
| S01 | Madde dili | 2, 2, 2 | ✓✓✓ |
| S02 | Madde dili | 2, 1, 1 | ✓✓✓ |
| S03 | Madde dili | 1, 1, 1 | ✓✓✓ |
| S04 | Madde dili | 1, 1, 1 | ✓✓✓ |
| S05 | Madde dili | 1, 1, 1 | ✓✓✓ |
| S06 | Madde dili | 14, 14, 12 | ✗✗✗ |
| S07 | Madde dili | 1, 1, 1 | ✓✓✓ |
| S08 | Günlük dil | 1, 2, 2 | ✓✓✓ |
| S09 | Günlük dil | 1, 1, 1 | ✓✓✓ |
| S10 | Günlük dil | 1, 1, 1 | ✓✓✓ |
| S11 | Günlük dil | 1, 1, 1 | ✓✓✓ |
| S12 | Günlük dil | 1, 1, 1 | ✓✓✓ |
| S13 | Günlük dil | 1, 1, 1 | ✓✓✓ |
| S14 | Günlük dil | 1, 1, 2 | ✓✓✓ |
| S15 | Günlük dil | 3, 1, 1 | ✓✓✓ |
| S16 | İki madde | 4/3, 4/5, 3/4 | ✓✓✓ |
| S17 | İki madde | 1/3, 1/2, 1/7 | ✓✓✗ |
| S18 | İki madde | 1/2, 1/2, 4/1 | ✓✓✓ |
| S19 | İki madde | 5/6, 5/6, 4/7 | ✗✗✗ |
| S20 | İki madde | 4/1, 6/8, 4/1 | ✓✗✓ |
| S21 | İki madde | 1/2, 1/2, 2/1 | ✓✓✓ |
| S26 | Madde numarası | 2, 1, 5 | ✓✓✓ |
| S27 | Madde numarası | 1, 1, 1 | ✓✓✓ |
| S28 | Madde numarası | 1, 1, 1 | ✓✓✓ |
| S29 | Madde numarası | 1, 1, 1 | ✓✓✓ |
| S30 | Madde numarası | 1, 1, 1 | ✓✓✓ |

## Koşu 1: üretilen sorgular ve uyarılar

| Soru | Sorgular / uyarı | Atılan |
|---|---|---|
| S01 | `mesafeli sözleşmelerde cayma hakkı süresi` · `cayma hakkının kullanılması bildirim süresi mesafeli satış` · `mesafeli sözleşmeler cayma hakkı kullanılma koşulları` |  |
| S02 | `ayıplı mal seçimlik haklar` · `tüketicinin ayıplı maldan dolayı sözleşmeden dönme hakkı` · `ayıplı malda bedel indirimi ve onarım talebi` |  |
| S03 | `ayıplı mal zamanaşımı süresi` · `satıcının ayıptan sorumluluğu zamanaşımı` · `tüketici ayıplı mal değişim onarım hakkı zamanaşımı` |  |
| S04 | `ticari elektronik ileti önceden onay` · `ticari elektronik iletişim izni alıcının rıza` · `elektronik ticaret ticari ileti gönderimi onay şartı` |  |
| S05 | `ilgili kişinin veri sorumlusuna başvuru hakları` · `kişisel verilerin işlenmesine ilişkin ilgili kişi hakları` · `veri sorumlusuna başvuru ve şikayet yolu` |  |
| S06 | `cayma hakkının kullanılamayacağı sözleşmeler` · `mesafeli sözleşmelerde cayma hakkı istisnaları` · `tüketicinin cayma hakkı kapsamı dışında kalan mal ve hizmetler` |  |
| S07 | `taksitli satış sözleşmesinde cayma hakkı` · `mesafeli sözleşmelerde cayma hakkı kullanım süresi` · `cayma hakkı süresinin başlangıcı` |  |
| S08 | `mesafeli sözleşmelerde cayma hakkı` · `mesafeli satışta malın iadesi ve cayma hakkı süresi` · `internetten satın alınan mal için cayma hakkının kullanılması` |  |
| S09 | `ayıplı mal ispat yükü satıcıya ait` · `tüketici sözleşmesinde ayıbın ortaya çıkma zamanı` · `satılan malın ayıplı olduğunun ispatı tüketici` |  |
| S10 | `mesafeli sözleşmede teslim süresi` · `satıcının edimi ifa etmemesi sözleşmeden dönme` · `siparişin teslim edilmemesi sözleşmeden dönme hakkı` |  |
| S11 | `talep edilmeden gönderilen mal veya hizmet` · `tüketicinin gönderilen mala ilişkin yükümlülüğü` · `sipariş dışı mal gönderimi ve bedel talebi` |  |
| S12 | `satıcının mal satma yükümlülüğü` · `mağazada ürünün satışından kaçınma ve tüketicinin hakları` · `vitrin ve ilan edilen fiyattan satış zorunluluğu` |  |
| S13 | `ticari elektronik ileti gönderiminden vazgeçme hakkı` · `ticari elektronik ileti onay ve ret bildirimi` · `ticari iletişim izni geri alınması` |  |
| S14 | `veri sorumlusunun ilgili kişi başvurusuna cevap verme süresi` · `kişisel verilere ilişkin bilgi talebi yanıt süresi` · `ilgili kişinin bilgi talep hakkı veri sorumlusu başvuru` |  |
| S15 | `piramit satış sistemi haksız ticari uygulama` · `zincir satış ve yeni üye kazandırmaya dayalı kazanç yasağı` · `aldatıcı ticari uygulamalar ve tüketicinin korunması` |  |
| S16 | `mesafeli sözleşmelerde cayma hakkı kullanım süresi` · `cayma hakkında malın geri gönderilmesi süresi` · `cayma hakkında satıcının bedeli iade etme süresi` |  |
| S17 | `garanti süresi içinde onarılan ayıplı mal` · `ayıplı malın onarımı sonrası tüketicinin seçimlik hakları` · `tüketici malında garanti belgesi ve garanti kapsamında onarım` |  |
| S18 | `tüketici hakem heyetine başvuru parasal sınır` · `tüketici uyuşmazlıklarında arabuluculuk dava şartı` · `tüketici mahkemesi görev parasal sınırı` |  |
| S19 | `mesafeli sözleşmelerde taşıma sırasında malın zararından satıcının sorumluluğu` · `satıcının siparişi teslim etme yükümlülüğü ve teslim süresi` · `mesafeli sözleşmede malın teslim edilmemesi halinde sözleşmeden dönme hakkı` |  |
| S20 | `mesafeli sözleşmelerde satıcının ön bilgilendirme yükümlülüğü` · `mesafeli sözleşmelerde ön bilgilerin teyidi` · `elektronik ticarette sözleşme öncesi bilgilendirme` |  |
| S21 | `kişisel verilerin silinmesi talebi` · `kişisel verilerin silinmesi ve yok edilmesi veri sorumlusuna başvuru` · `veri sorumlusuna başvuru usul ve esasları` |  |
| S22 | `kira sözleşmesinde depozito iadesi` · `kiralananın teslimi sonrası teminatın iadesi` · `konut kira sözleşmesinde güvence bedelinin iadesi süresi` |  |
| S23 | `internet üzerinden yapılan satışlarda katma değer vergisi oranı` · `elektronik ticaret mal satışı katma değer vergisi uygulaması` |  |
| S24 | `kıdem tazminatı hesaplanması` · `iş sözleşmesinin feshi halinde kıdem tazminatı` · `işçinin kıdem tazminatına hak kazanma şartları` |  |
| S25 | `trafik idari para cezasına itiraz süresi` · `trafik cezasına karşı sulh ceza hakimliğine itiraz` |  |
| S26 | `6502 sayılı Kanun madde 56` · `tüketici sözleşmelerinde cayma hakkı ve istisnalar` |  |
| S27 | `KVKK madde 5 kişisel verilerin işlenme şartları` · `6698 sayılı Kanun madde 5 kişisel verilerin işlenmesi` |  |
| S28 | `Elektronik Ticaretin Düzenlenmesi Hakkında Kanun ek madde 2` · `elektronik ticaret kanunu ek madde 2 düzenleme konusu` |  |
| S29 | `Mesafeli Sözleşmeler Yönetmeliği madde 15` · `mesafeli sözleşmelerde cayma hakkının istisnaları` · `mesafeli sözleşmelerde cayma hakkı kullanılamayan haller` |  |
| S30 | `Tüketicinin Korunması Hakkında Kanun madde 73/A` · `tüketicinin korunması hakkında kanun 73/A hükmü` · `tüketici hakem heyeti ve tüketici mahkemesi başvuru usulü` |  |
