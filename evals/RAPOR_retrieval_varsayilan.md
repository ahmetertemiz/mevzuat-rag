# Varsayılan hat değerlendirmesi: retrieval

`python scripts/eval_retrieval.py --set evals/retrieval.yaml --varsayilan` ile üretildi. Hat: `bm25` + yeniden yazım (`claude-opus-5-5`, prompt v2), önbelleksiz, tek koşu.

| @1 | @3 | @5 | Yeniden yazım başarısız | Toplam maliyet |
|---|---|---|---|---|
| 15/26 | 22/26 | 25/26 | 0 | $0.2270 |

| Tür | n | @1 | @3 | @5 |
|---|---|---|---|---|
| Madde dili | 7 | 5 | 6 | 6 |
| Günlük dil | 8 | 6 | 8 | 8 |
| İki madde | 6 | 0 | 3 | 6 |
| Madde numarası | 5 | 4 | 5 | 5 |

| Soru | Tür | Sıra | İlk 3 | Sorgular / uyarı |
|---|---|---|---|---|
| S01 | Madde dili | 2 | TKHK:18, MSY:9, MSY:10 | `mesafeli sözleşmelerde cayma hakkı süresi` · `cayma süresinin başlangıcı malın teslimi` · `cayma hakkı ondört gün içinde gerekçe göstermeksizin` |
| S02 | Madde dili | 1 | TKHK:11, TKHK:15, TKHK:57 | `ayıplı mal tüketicinin seçimlik hakları` · `ayıplı malda sözleşmeden dönme bedel indirimi ücretsiz onarım` · `ayıpsız misli ile değiştirme hakkı` |
| S03 | Madde dili | 1 | TKHK:12, TKHK:16, TKHK:10 | `ayıplı maldan sorumluluk zamanaşımı süresi` · `ayıplı mal iki yıllık zamanaşımı teslim tarihi` · `ayıbın ağır kusur veya hile ile gizlenmesi zamanaşımı` |
| S04 | Madde dili | 1 | ETK:6, ETK:8, ETK:7 | `ticari elektronik ileti gönderiminde alıcının önceden onayı` · `ticari elektronik ileti onay alınmadan gönderilebilecek haller` · `ticari elektronik ileti onayının alınma şekli ve ispatı` |
| S05 | Madde dili | 1 | KVKK:11, KVKK:9, KVKK:16 | `ilgili kişinin hakları kişisel verilerin işlenmesi` · `veri sorumlusuna başvuru hakkı` · `kişisel verilerin silinmesi düzeltilmesi talebi` · `veri sorumlusuna başvuru usulü ve cevap süresi` |
| S06 | Madde dili | 9 | MSY:11, MSY:Ek, TKHK:18 | `cayma hakkının istisnaları` · `cayma hakkı kullanılamayacak sözleşmeler mesafeli sözleşmeler` · `tüketicinin özel istekleri doğrultusunda hazırlanan mallar cayma hakkı` |
| S07 | Madde dili | 1 | TKHK:18, TKHK:43, TKHK:21 | `taksitle satış sözleşmesinde cayma hakkı süresi` · `taksitle satış sözleşmesinden cayma bildirimi` · `taksitle satış sözleşmesi cayma hakkı on dört gün` |
| S08 | Günlük dil | 1 | MSY:9, TKHK:24, MSY:11 | `mesafeli sözleşmelerde cayma hakkı` · `cayma hakkı süresi on dört gün mal teslimi` · `cayma hakkı kullanımında bedel iadesi` |
| S09 | Günlük dil | 1 | TKHK:10, TKHK:11, TKHK:74 | `ayıplı malda ispat yükü teslimden itibaren altı ay` · `ayıbın teslim tarihinde var olduğu karinesi` · `ayıplı mal tüketicinin seçimlik hakları` · `garanti süresi içinde arıza kullanım hatası` |
| S10 | Günlük dil | 2 | MSY:9, MSY:16, TKHK:30 | `mesafeli sözleşmelerde satıcının ifa süresi otuz gün` · `siparişin süresinde teslim edilmemesi sözleşmenin feshi` · `malın teslimi ifa süresinin aşılması bedel iadesi` |
| S11 | Günlük dil | 1 | TKHK:7, MSY:6, TKHK:47/A | `sipariş edilmeyen mal ve hizmet ödeme yükümlülüğü` · `talep edilmeyen mal gönderilmesi tüketicinin sorumluluğu` · `ataletle kabul sessiz kalma sözleşme kurulmaz` |
| S12 | Günlük dil | 1 | TKHK:6, TKHK:74, TKHK:17 | `satıştan kaçınma yasağı` · `vitrinde teşhir edilen malın satışından kaçınma` · `satışa sunulan malın tüketiciye satılması zorunluluğu` |
| S13 | Günlük dil | 1 | ETK:8, ETK:2, ETK:11 | `ticari elektronik ileti onay şartı` · `ticari elektronik iletiyi reddetme hakkı` · `ret bildirimi sonrası ileti gönderiminin durdurulması süresi` · `ileti yönetim sistemi onayın geri alınması` |
| S14 | Günlük dil | 3 | KVKK:15, KVKK:14, KVKK:13 | `ilgili kişinin veri sorumlusuna başvurusu cevaplama süresi` · `veri sorumlusuna başvuru otuz gün içinde sonuçlandırma` · `ilgili kişinin kişisel verileri hakkında bilgi talep etme hakkı` |
| S15 | Günlük dil | 1 | TKHK:80, TKHK:47/A, TKHK:77 | `piramit satış sistemi yasağı` · `doğrudan satış sistemi yeni katılımcı getirme kazanç` · `piramit satış sistemi tanımı ve unsurları` |
| S16 | İki madde | 5, 1 | MSY:12, MSY:12/A, TKHK:43 | `cayma hakkı kullanıldığında tüketicinin malı geri gönderme süresi` · `cayma bildiriminden itibaren malın satıcıya iadesi` · `cayma hakkında satıcının bedeli iade yükümlülüğü süresi` · `mesafeli sözleşmede cayma halinde ödemelerin iadesi` |
| S17 | İki madde | 2, 3 | TKHK:57, TKHK:56, TKHK:11 | `garanti süresi içinde arızanın tekrarlanması` · `ayıplı mal tüketicinin seçimlik hakları` · `onarım sonrası malın yenisiyle değiştirilmesi bedel iadesi` · `garanti belgesi onarım süresi` |
| S18 | İki madde | 2, 1 | TKHK:73/A, TKHK:68, TKHK:70 | `tüketici hakem heyetine başvuru parasal sınır` · `tüketici hakem heyetlerinin görev alanı değeri` · `tüketici uyuşmazlıklarında dava şartı arabuluculuk` · `tüketici mahkemesinde dava açmadan önce arabulucuya başvuru zorunluluğu` |
| S19 | İki madde | 4, 5 | MSY:12/A, MSY:12, MSY:9 | `mesafeli sözleşmede malın kaybolması veya hasarından satıcının sorumluluğu` · `taşıyıcıya teslimde hasar ve kayıp riski` · `mesafeli sözleşmelerde malın teslim süresi otuz gün` · `teslim süresinin aşılması durumunda tüketicinin sözleşmeyi feshi` |
| S20 | İki madde | 5, 2 | TKHK:48, MSY:7, MSY:12/A | `mesafeli sözleşmelerde ön bilgilendirme yükümlülüğü` · `ön bilgilendirme içeriği satıcı bilgileri cayma hakkı` · `ön bilgilendirmenin teyidi elektronik ortamda` · `ön bilgilerin alındığının tüketici tarafından onaylanması ispat yükü` |
| S21 | İki madde | 1, 3 | KVKK:7, KVKK:11, KVKK:13 | `kişisel verilerin silinmesi yok edilmesi anonim hale getirilmesi` · `ilgili kişinin hakları kişisel verilerin silinmesini isteme` · `veri sorumlusuna başvuru usul ve esasları` · `ilgili kişinin veri sorumlusuna yazılı başvurusu ve cevap süresi` |
| S22 | Cevapsız | — | TKHK:42, TKHK:45, TKHK:43 | `kira sözleşmesinde güvence bedelinin iadesi` · `kiracının güvenlik teminatının geri verilmesi süresi` · `konut kirasında güvence bedeli ve kiraya verenin yükümlülüğü` |
| S23 | Cevapsız | — | ETK:Ek 2, TKHK:54, TKHK:77 | `elektronik ticarette katma değer vergisi oranı` · `mesafeli satış sözleşmesinde vergiler dahil toplam fiyat` · `ön bilgilendirmede malın tüm vergiler dahil fiyatı` |
| S24 | Cevapsız | — | KVKK:27, TKHK:37, TKHK:1 | `kıdem tazminatı hesaplanması` · `iş sözleşmesinin işveren tarafından feshi kıdem tazminatı` · `kıdem tazminatına esas ücret ve hizmet süresi` |
| S25 | Cevapsız | — | ETK:12, TKHK:78, TKHK:70 | `trafik idari para cezasına itiraz süresi` · `idari yaptırım kararına karşı sulh ceza hakimliğine başvuru süresi` · `2918 sayılı Karayolları Trafik Kanunu itiraz` |
| S26 | Madde numarası | 1 | TKHK:56, TKHK:86, TKHK:83 | `6502 sayılı Kanun madde 56` · `6502 sayılı Tüketicinin Korunması Hakkında Kanun 56. madde` |
| S27 | Madde numarası | 1 | KVKK:5, KVKK:4, KVKK:3 | `KVKK madde 5 kişisel verilerin işlenme şartları` · `6698 sayılı Kanun madde 5 açık rıza` · `açık rıza aranmaksızın kişisel veri işlenmesi halleri` |
| S28 | Madde numarası | 1 | ETK:Ek 2, ETK:1, ETK:Geçici 1 | `Elektronik Ticaretin Düzenlenmesi Hakkında Kanun ek madde 2` · `6563 sayılı Kanun ek madde 2` · `elektronik ticaret pazar yeri hizmet sağlayıcı yükümlülükleri` |
| S29 | Madde numarası | 1 | MSY:15, TKHK:49, MSY:1 | `Mesafeli Sözleşmeler Yönetmeliği madde 15` · `mesafeli sözleşmelerde cayma hakkının istisnaları` |
| S30 | Madde numarası | 2 | TKHK:86, TKHK:73/A, TKHK:2 | `Tüketicinin Korunması Hakkında Kanun madde 73/A` · `6502 sayılı Kanun madde 73/A` · `6502 sayılı Kanun ek madde idari yaptırım` |
