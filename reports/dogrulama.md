# Belge işleme doğrulama raporu

`python scripts/build_chunks.py` tarafından üretilir. Elle düzenlemeyin.

Toplam parça: **217** (indekse girecek: 217, indeks dışı: 0)

## 1. Belge başına özet

| Belge | Madde (ayrıştırılan / bağımsız sayım) | Parça | Bölünen madde | Mülga madde | Dipnot (bağlanan / toplam) | Tablo | Ek |
|---|---|---|---|---|---|---|---|
| TKHK (6502) | 95 / 95 ✅ | 109 | 8 | 0 | 32 / 32 | 1 | 0 |
| ETK (6563) | 22 / 22 ✅ | 36 | 6 | 1 | 5 / 5 | 1 | 0 |
| KVKK (6698) | 36 / 36 ✅ | 41 | 3 | 0 | 8 / 8 | 0 | 0 |
| MSY (20237) | 25 / 25 ✅ | 31 | 5 | 0 | 4 / 4 | 0 | 1 |

*Bağımsız sayım:* paragraf mantığı kullanılmadan, ham sayfa metninde satır başındaki `MADDE n –` kalıbı sayıldı.

## 2. Belge üstverisi

| Belge | Tam ad | Kabul | RG tarih / sayı | İndirme | PDF oluşturma | En son metin içi değişiklik notu | Dipnotlarda geçen en geç tarih |
|---|---|---|---|---|---|---|---|
| TKHK | 6502 sayılı Tüketicinin Korunması Hakkında Kanun | 2013-11-07 | 2013-11-28 / 28835 | 2026-11-23 | 2026-07-01 | 2026-06-24 `(Değişik:24/6/2026-7587/24 md.)` | 2027-03-02 (dipnot 14) |
| ETK | 6563 sayılı Elektronik Ticaretin Düzenlenmesi Hakkında Kanun | 2014-10-23 | 2014-11-05 / 29166 | 2026-11-23 | 2026-06-02 | 2024-10-24 `(Değişik:24/10/2024-7529/9 md.)` | 2027-03-02 (dipnot 2) |
| KVKK | 6698 sayılı Kişisel Verilerin Korunması Kanunu | 2016-03-24 | 2016-04-07 / 29677 | 2026-11-23 | 2024-06-03 | 2024-03-02 `(Mülga:2/3/2024-7499/33 md.)` | 2024-03-02 (dipnot 1) |
| MSY | Mesafeli Sözleşmeler Yönetmeliği | — | 2014-11-27 / 29188 | 2026-11-23 | 2026-07-30 | 2025-05-24 `(Değişik:RG-24/5/2025-32909)` | 2026-01-01 (dipnot 4) |

MSY değiştiren yönetmelikler listesinin son satırı: 2025-05-24, RG sayı 32909.

*Not:* "Dipnotlarda geçen en geç tarih" ileri bir tarih olabilir (ör. AYM iptal kararının yürürlüğe gireceği gün). Bu bir değişiklik tarihi değil, belgede geçen en geç tarihtir.

## 3. Parça uzunlukları (kelime, `metin` alanı)

| Belge | En kısa | Medyan | En uzun |
|---|---|---|---|
| TKHK | 7 (`TKHK-m88-1`) | 114 | 349 (`TKHK-m63-1`) |
| ETK | 5 (`ETK-m10-1`) | 154 | 352 (`ETK-ek4-1`) |
| KVKK | 7 (`KVKK-m33-1`) | 149 | 332 (`KVKK-m21-1`) |
| MSY | 8 (`MSY-m23-1`) | 77 | 342 (`MSY-m4-1`) |

Tüm belgelerde en kısa 5: `ETK-m10-1` (5), `ETK-m15-1` (7), `ETK-m16-1` (7), `KVKK-m33-1` (7), `TKHK-m88-1` (7)

Tüm belgelerde en uzun 5: `ETK-m12-1` (346), `TKHK-m51-1` (349), `TKHK-m63-1` (349), `ETK-m12-2` (351), `ETK-ek4-1` (352)

Parça sınırı 350 kelime. Bölünen parçalara bağlam için fıkranın giriş cümlesi eklendiğinden sınır biraz aşılabilir.

## 4. Boş ya da şüpheli parçalar

Yok.

## 5. Yapısal bilgi notları

- **15 kelimeden kısa parçalar** (hata değil; yürürlük/yürütme gibi tek cümlelik maddeler): `ETK-m10-1` (5), `ETK-m15-1` (7), `ETK-m16-1` (7), `KVKK-m33-1` (7), `TKHK-m88-1` (7), `MSY-m23-1` (8), `KVKK-m31-1` (10), `MSY-m22-1` (11), `TKHK-m87-1` (11), `MSY-m1-1` (12), `TKHK-m2-1` (12), `ETK-m14-1` (14)
- Aşağıdaki başlıksız maddeler ve fıkra atlamaları PDF'le karşılaştırıldı: geçici maddelerin PDF'te de başlığı yok; KVKK m.30'da fıkralar PDF'te "(2) ila (5) - (… ile ilgili olup yerine işlenmiştir.)" biçiminde tek satırda.
- **TKHK** başlıksız maddeler: Geçici Madde 2, Geçici Madde 3
- **KVKK** başlıksız maddeler: Geçici Madde 2, Geçici Madde 3
- **KVKK** fıkra numarası atlayan maddeler: Madde 30 [1, 2, 6, 7]

## 6. İndekse alınmayan ek bölümler

- **TKHK**: Değişiklik/yürürlük tarihleri listesi (tarihçe; madde metni değil)
- **ETK**: Değişiklik/yürürlük tarihleri listesi (tarihçe; madde metni değil)
- **KVKK**: Değişiklik/yürürlük tarihleri listesi (tarihçe; madde metni değil)
- **KVKK**: Kadro cetveli (teşkilat kadro listesi)
- **MSY**: Resmî Gazete yayım/değişiklik listesi (yalnızca belge üstverisine işlendi)

## 7. İdari para cezası tabloları

Rakamlar sayfa görüntüleriyle karşılaştırıldı. Bir tablo yalnızca kullanıcı onayından sonra indekse girer (`build.py` içindeki `APPROVED_TABLES`). Her satır, karşılık geldiği madde parçasına `ilgili_parca` alanıyla bağlıdır.

### TKHK: 6502 Sayılı Tüketicinin Korunması Hakkında Kanunun 77 nci Maddesindeki İdari Para Cezaları Miktarlarıyla İlgili Tablo

- Yıl: **2026** · PDF sayfaları: 48, 49, 50
- Açıklama: (23/12/2025 tarihli ve 33116 sayılı Resmî Gazete’de yayımlanan 6502 Sayılı Tüketicinin Korunması Hakkında Kanunun 77 nci Maddesine Göre 2026 Yılında Uygulanacak Olan İdari Para Cezalarına İlişkin Tebliği ile 6502 sayılı Tüketicinin Korunması Hakkında Kanunun 77 nci maddesinde düzenlenmiş olan idari para cezaları miktarları, 1/1/2026 tarihinden itibaren aşağıdaki şekilde uygulanacaktır.)
- Otomatik kontrol: hücrelerden okunan 67 sayı ile tutar sütunundaki ham kelimelerden okunan 67 sayı **aynı** ✅
- Durum: **indekste** (onaylandı)
- İlgili parçalar: `TKHK-m77-1`, `TKHK-m77-2`, `TKHK-m77-3`, `TKHK-m77-4`, `TKHK-m77-5`, `TKHK-m77-6`, `TKHK-m77-7`, `TKHK-gecici3-1`
- Sayfa görüntüleri: [TKHK_tablo_s48.png](img/TKHK_tablo_s48.png), [TKHK_tablo_s49.png](img/TKHK_tablo_s49.png), [TKHK_tablo_s50.png](img/TKHK_tablo_s50.png)

| # | Bölüm | Fıkra | Bent | Alt bent | Tutar (TL) | Sayfa | İlgili parça |
|---|---|---|---|---|---|---|---|
| 1 | güncel | Birinci fıkrasındaki ceza miktarı | (a) bendi |  | 3.973 | 48 | `TKHK-m77-1` |
| 2 | güncel | Birinci fıkrasındaki ceza miktarı | (b) bendi |  | 3.973 | 48 | `TKHK-m77-1` |
| 3 | güncel | İkinci fıkrasındaki ceza miktarı |  |  | 3.922 | 48 | `TKHK-m77-1` |
| 4 | güncel | Üçüncü fıkrasındaki ceza miktarı |  |  | 19.827 | 49 | `TKHK-m77-1` |
| 5 | güncel | Dördüncü fıkrasındaki ceza miktarı | (a) bendi |  | 31.902.048 | 49 | `TKHK-m77-2` |
| 6 | güncel | Dördüncü fıkrasındaki ceza miktarı | (a) bendi |  | 22.329 | 49 | `TKHK-m77-2` |
| 7 | güncel | Beşinci fıkrasındaki ceza miktarı |  |  | 1.987.014 | 49 | `TKHK-m77-2` |
| 8 | güncel | Beşinci fıkrasındaki ceza miktarı |  |  | 446.627 | 49 | `TKHK-m77-2` |
| 9 | güncel | Altıncı fıkrasındaki ceza miktarı |  |  | 3.922 | 49 | `TKHK-m77-2` |
| 10 | güncel | Yedinci fıkrasındaki ceza miktarı |  |  | 1.987.014 | 49 | `TKHK-m77-2` |
| 11 | güncel | Sekizinci fıkrasındaki ceza miktarları |  |  | 99.352.237 | 49 | `TKHK-m77-2` |
| 12 | güncel | Sekizinci fıkrasındaki ceza miktarları |  |  | 9.935.181 | 49 | `TKHK-m77-2` |
| 13 | güncel | Dokuzuncu fıkrasındaki ceza miktarları |  |  | 99.315 | 49 | `TKHK-m77-3` |
| 14 | güncel | Dokuzuncu fıkrasındaki ceza miktarları |  |  | 1.987.014 | 49 | `TKHK-m77-3` |
| 15 | güncel | Dokuzuncu fıkrasındaki ceza miktarları |  |  | 198.656 | 49 | `TKHK-m77-3` |
| 16 | güncel | Onuncu fıkrasındaki ceza miktarları | (a) bendi |  | 3.190.204 | 49 | `TKHK-m77-3` |
| 17 | güncel | Onuncu fıkrasındaki ceza miktarları | (a) bendi |  | 3.187 | 49 | `TKHK-m77-3` |
| 18 | güncel | Onuncu fıkrasındaki ceza miktarları | (b) bendi | 1. alt bent | 2.013.887 | 49 | `TKHK-m77-3` |
| 19 | güncel | Onuncu fıkrasındaki ceza miktarları | (b) bendi | 1. alt bent | 32.510 | 49 | `TKHK-m77-3` |
| 20 | güncel | Onuncu fıkrasındaki ceza miktarları | (b) bendi | 2. alt bent | 32.510 | 49 | `TKHK-m77-3` |
| 21 | güncel | Onuncu fıkrasındaki ceza miktarları | (b) bendi | 3. alt bent | 223.965 | 49 | `TKHK-m77-3` |
| 22 | güncel | Onuncu fıkrasındaki ceza miktarları | (c) bendi |  | 3.973 | 49 | `TKHK-m77-3` |
| 23 | güncel | On birinci fıkrasındaki ceza miktarı |  |  | 198.656 | 49 | `TKHK-m77-3` |
| 24 | güncel | On ikinci fıkrasındaki ceza miktarı | (a) bendi |  | 198.679 | 49 | `TKHK-m77-4` |
| 25 | güncel | On ikinci fıkrasındaki ceza miktarı | (a) bendi |  | 1.986.795 | 49 | `TKHK-m77-4` |
| 26 | güncel | On ikinci fıkrasındaki ceza miktarı | (b) bendi |  | 3.991.652 | 49 | `TKHK-m77-4` |
| 27 | güncel | On ikinci fıkrasındaki ceza miktarı | (b) bendi |  | 39.916.524 | 49 | `TKHK-m77-4` |
| 28 | güncel | On ikinci fıkrasındaki ceza miktarı | (c) bendi |  | 99.339 | 49 | `TKHK-m77-4` |
| 29 | güncel | On ikinci fıkrasındaki ceza miktarı | (c) bendi |  | 993.397 | 49 | `TKHK-m77-4` |
| 30 | güncel | On ikinci fıkrasındaki ceza miktarı | (c) bendi |  | 1.995.826 | 49 | `TKHK-m77-4` |
| 31 | güncel | On ikinci fıkrasındaki ceza miktarı | (c) bendi |  | 19.958.262 | 49 | `TKHK-m77-4` |
| 32 | güncel | On ikinci fıkrasındaki ceza miktarı | (ç) bendi |  | 108.370 | 49 | `TKHK-m77-4` |
| 33 | güncel | On ikinci fıkrasındaki ceza miktarı | (ç) bendi |  | 1.083.706 | 49 | `TKHK-m77-4` |
| 34 | güncel | On ikinci fıkrasındaki ceza miktarı | (d) bendi |  | 1.083.706 | 49 | `TKHK-m77-4` |
| 35 | güncel | On ikinci fıkrasındaki ceza miktarı | (d) bendi |  | 10.837.065 | 49 | `TKHK-m77-4` |
| 36 | güncel | On ikinci fıkrasındaki ceza miktarı | (e) bendi |  | 1.083.706 | 49 | `TKHK-m77-4` |
| 37 | güncel | On ikinci fıkrasındaki ceza miktarı | (e) bendi |  | 10.837.065 | 49 | `TKHK-m77-4` |
| 38 | güncel | On ikinci fıkrasındaki ceza miktarı | (f) bendi |  | 505.729 | 49 | `TKHK-m77-4` |
| 39 | güncel | On ikinci fıkrasındaki ceza miktarı | (f) bendi |  | 5.057.297 | 49 | `TKHK-m77-4` |
| 40 | güncel | On ikinci fıkrasındaki ceza miktarı | (g) bendi |  | 108.370 | 49 | `TKHK-m77-5` |
| 41 | güncel | On ikinci fıkrasındaki ceza miktarı | (g) bendi |  | 1.083.706 | 49 | `TKHK-m77-5` |
| 42 | güncel | On üçüncü fıkrasındaki ceza miktarları |  |  | 108.370 | 49 | `TKHK-m77-6` |
| 43 | güncel | On üçüncü fıkrasındaki ceza miktarları |  |  | 1.083.706 | 49 | `TKHK-m77-6` |
| 44 | güncel | On üçüncü fıkrasındaki ceza miktarları |  |  | 1.083.706 | 49 | `TKHK-m77-6` |
| 45 | güncel | On üçüncü fıkrasındaki ceza miktarları |  |  | 10.837.065 | 49 | `TKHK-m77-6` |
| 46 | güncel | On dördüncü fıkrasındaki ceza miktarları |  |  | 6.380.408 | 49 | `TKHK-m77-6` |
| 47 | güncel | On dördüncü fıkrasındaki ceza miktarları |  |  | 1.987.014 | 49 | `TKHK-m77-6` |
| 48 | güncel | On dördüncü fıkrasındaki ceza miktarları |  |  | 99.315 | 50 | `TKHK-m77-6` |
| 49 | güncel | On beşinci fıkrasındaki ceza miktarları |  |  | 510.430 | 50 | `TKHK-m77-6` |
| 50 | güncel | On beşinci fıkrasındaki ceza miktarları |  |  | 10.837.065 | 50 | `TKHK-m77-6` |
| 51 | güncel | On beşinci fıkrasındaki ceza miktarları |  |  | 1.806.177 | 50 | `TKHK-m77-6` |
| 52 | güncel | On beşinci fıkrasındaki ceza miktarları |  |  | 90.308 | 50 | `TKHK-m77-6` |
| 53 | güncel | On beşinci fıkrasındaki ceza miktarları |  |  | 19.141.229 | 50 | `TKHK-m77-6` |
| 54 | güncel | On altıncı fıkrasındaki ceza miktarı |  |  | 3.922 | 50 | `TKHK-m77-6` |
| 55 | güncel | On yedinci fıkrasındaki ceza miktarı | (a) bendi |  | 6.274.500 | 50 | `TKHK-m77-7` |
| 56 | güncel | On yedinci fıkrasındaki ceza miktarı | (a) bendi |  | 2.760 | 50 | `TKHK-m77-7` |
| 57 | güncel | On yedinci fıkrasındaki ceza miktarı | (b) bendi |  | 1.254.900 | 50 | `TKHK-m77-7` |
| 58 | güncel | On sekizinci fıkrasındaki ceza miktarının alt ve üst sınırları |  |  | 19.827-738.286 | 50 | `TKHK-m77-7` |
| 59 | güncel | On dokuzuncu fıkrasındaki ceza miktarının alt ve üst sınırları |  |  | 510.430-765.649.243 | 50 | `TKHK-m77-7` |
| 60 | Geçici m.3 (değişiklik öncesi 77. madde) | Üçüncü fıkrasındaki ceza miktarı |  |  | 19.827 | 50 | `TKHK-gecici3-1` |
| 61 | Geçici m.3 (değişiklik öncesi 77. madde) | Dördüncü fıkrasındaki ceza miktarları |  |  | 397.376 | 50 | `TKHK-gecici3-1` |
| 62 | Geçici m.3 (değişiklik öncesi 77. madde) | Dördüncü fıkrasındaki ceza miktarları |  |  | 19.827 | 50 | `TKHK-gecici3-1` |
| 63 | Geçici m.3 (değişiklik öncesi 77. madde) | Beşinci fıkrasındaki ceza miktarı |  |  | 1.987.014 | 50 | `TKHK-gecici3-1` |
| 64 | Geçici m.3 (değişiklik öncesi 77. madde) | Sekizinci fıkrasındaki ceza miktarları |  |  | 9.935.181 | 50 | `TKHK-gecici3-1` |
| 65 | Geçici m.3 (değişiklik öncesi 77. madde) | On dokuzuncu fıkrasındaki ceza miktarının alt sınırı |  |  | 496.719 | 50 | `TKHK-gecici3-1` |

### ETK: 6563 Sayılı Elektronik Ticaretin Düzenlenmesi Hakkında Kanunun 12 nci Maddesine Göre 2026 Yılında Uygulanacak Olan İdari Para Cezalarına İlişkin Tablo

- Yıl: **2026** · PDF sayfaları: 19
- Açıklama: 6563 sayılı Kanunun 12 nci maddesinde düzenlenen 1/1/2026 ile 31/12/2026 tarihleri arasında uygulanacak idari para cezası miktarları; Ticaret Bakanlığının 25/12/2025 tarihli ve 33118 sayılı Resmî Gazete’de yayımlanan Tebliği ile aşağıdaki şekilde düzenlenmiştir.
- Otomatik kontrol: hücrelerden okunan 31 sayı ile tutar sütunundaki ham kelimelerden okunan 31 sayı **aynı** ✅
- Durum: **indekste** (onaylandı)
- İlgili parçalar: `ETK-m12-1`, `ETK-m12-2`, `ETK-m12-3`, `ETK-m12-4`, `ETK-m12-5`
- Sayfa görüntüleri: [ETK_tablo_s19.png](img/ETK_tablo_s19.png)

| # | Bölüm | Fıkra | Bent | Alt bent | Tutar (TL) | Sayfa | İlgili parça |
|---|---|---|---|---|---|---|---|
| 1 | güncel | Birinci fıkrasının (a) bendindeki cezanın alt ve üst sınırları |  |  | 2.859-14.309 | 19 | `ETK-m12-1` |
| 2 | güncel | Birinci fıkrasının (b) bendindeki cezanın alt ve üst sınırları |  |  | 2.859-28.620 | 19 | `ETK-m12-1` |
| 3 | güncel | Birinci fıkrasının (c) bendindeki cezanın alt ve üst sınırları |  |  | 5.723-42.930 | 19 | `ETK-m12-1` |
| 4 | güncel | Birinci fıkrasının (ç) bendindeki cezanın alt ve üst sınırları |  |  | 28.620-286.206 | 19 | `ETK-m12-1` |
| 5 | güncel | Birinci fıkrasının (d) bendindeki cezanın alt ve üst sınırları |  |  | 28.620-286.206 | 19 | `ETK-m12-1` |
| 6 | güncel | Birinci fıkrasının (e) bendindeki cezanın alt ve üst sınırları |  |  | 143.102-715.516 | 19 | `ETK-m12-1` |
| 7 | güncel | Birinci fıkrasının (f) bendindeki cezanın alt ve üst sınırları |  |  | 143.102-715.516 | 19 | `ETK-m12-1` |
| 8 | güncel | Birinci fıkrasının (g) bendindeki cezanın alt ve üst sınırları |  |  | 28.620-286.206 | 19 | `ETK-m12-1` |
| 9 | güncel | Birinci fıkrasındaki ceza tutarları | (ğ) bendi |  | En az 28.620 | 19 | `ETK-m12-1` |
| 10 | güncel | Birinci fıkrasındaki ceza tutarları | (h) bendi |  | 1.431.033 | 19 | `ETK-m12-2` |
| 11 | güncel | Birinci fıkrasındaki ceza tutarları | (ı) bendi |  | 28.620 | 19 | `ETK-m12-2` |
| 12 | güncel | Birinci fıkrasındaki ceza tutarları | (j) bendi |  | 858.620 | 19 | `ETK-m12-2` |
| 13 | güncel | Birinci fıkrasındaki ceza tutarları | (l) bendi |  | En az 286.206 | 19 | `ETK-m12-2` |
| 14 | güncel | Birinci fıkrasındaki ceza tutarları | (m) bendi |  | 28.620 | 19 | `ETK-m12-2` |
| 15 | güncel | Birinci fıkrasındaki ceza tutarları | (o) bendi |  | 28.620.688 | 19 | `ETK-m12-2` |
| 16 | güncel | Birinci fıkrasındaki ceza tutarları | (ö) bendi |  | 2.862.067 | 19 | `ETK-m12-2` |
| 17 | güncel | Birinci fıkrasındaki ceza tutarları | (p) bendi |  | 2.862.067 | 19 | `ETK-m12-2` |
| 18 | güncel | Birinci fıkrasındaki ceza tutarları | (s) bendi |  | 715.516 | 19 | `ETK-m12-3` |
| 19 | güncel | Birinci fıkrasındaki ceza tutarları | (ş) bendi |  | 57.241.378 | 19 | `ETK-m12-3` |
| 20 | güncel | Üçüncü fıkrasındaki ceza tutarları |  |  | 28.620.688 | 19 | `ETK-m12-4` |
| 21 | güncel | Üçüncü fıkrasındaki ceza tutarları |  |  | 57.241.378 | 19 | `ETK-m12-4` |
| 22 | güncel | Üçüncü fıkrasındaki ceza tutarları |  |  | 114.482.758 | 19 | `ETK-m12-4` |
| 23 | güncel | Altıncı fıkrasındaki ceza tutarı |  |  | En fazla 1.431.034.488 | 19 | `ETK-m12-5` |

**Bilinen sınır (6502 tablosu):** Bazı satırlarda aynı fıkra/bent için birden çok tutar var (ör. dördüncü fıkra (a) bendi: 31.902.048 ve 22.329). Tablo hangi tutarın hangi duruma ait olduğunu söylemiyor; bu bilgi 77. maddenin metninde. Tutarlar tabloda göründüğü sırayla tutuluyor.

## 8. Rastgele örnekler (belge başına 3, seed=2026)

### `TKHK-m15-1`

- **Bağlam başlığı:** 6502 sayılı Tüketicinin Korunması Hakkında Kanun (TKHK) · Madde 15 · Tüketicinin seçimlik hakları
- **Madde:** Madde 15 · **Başlık:** Tüketicinin seçimlik hakları · **Fıkralar:** [1, 2, 3, 4] · **Bentler:** None · **Parça:** 1/1 · **Sayfa:** [7, 8]
- **Kısım/Bölüm:** Üçüncü Kısım: Ayıplı Mal ve Hizmetler / İkinci Bölüm: Ayıplı Hizmetler
- **Değişiklik notları:** —

```text
(1) Hizmetin ayıplı ifa edildiği durumlarda tüketici, hizmetin yeniden görülmesi, hizmet sonucu ortaya çıkan eserin ücretsiz onarımı, ayıp oranında bedelden indirim veya sözleşmeden dönme haklarından birini sağlayıcıya karşı kullanmakta serbesttir. Sağlayıcı, tüketicinin tercih ettiği bu talebi yerine getirmekle yükümlüdür. Seçimlik hakların kullanılması nedeniyle ortaya çıkan tüm masraflar sağlayıcı tarafından karşılanır. Tüketici, bu seçimlik haklarından biri ile birlikte Türk Borçlar Kanunu hükümleri uyarınca tazminat da talep edebilir.
(2) Ücretsiz onarım veya hizmetin yeniden görülmesinin sağlayıcı için orantısız güçlükleri beraberinde getirecek olması hâlinde tüketici bu hakları kullanamaz. Orantısızlığın tayininde hizmetin ayıpsız değeri, ayıbın önemi ve diğer seçimlik haklara başvurmanın tüketici açısından sorun teşkil edip etmeyeceği gibi hususlar dikkate alınır.
(3) Tüketicinin sözleşmeden dönme veya ayıp oranında bedelden indirim hakkını seçtiği durumlarda, ödemiş olduğu bedelin tümü veya bedelden indirim yapılan tutar derhâl tüketiciye iade edilir.
(4) Ücretsiz onarım veya hizmetin yeniden görülmesinin seçildiği hâllerde, hizmetin niteliği ve tüketicinin bu hizmetten yararlanma amacı dikkate alındığında, makul sayılabilecek bir süre içinde ve tüketici için ciddi sorunlar doğurmayacak şekilde bu talep sağlayıcı tarafından yerine getirilir. Her hâlükârda bu süre talebin sağlayıcıya yöneltilmesinden itibaren otuz iş gününü geçemez. Aksi takdirde tüketici diğer seçimlik haklarını kullanmakta serbesttir.
```

### `TKHK-m40-1`

- **Bağlam başlığı:** 6502 sayılı Tüketicinin Korunması Hakkında Kanun (TKHK) · Madde 40 · Ön ödemeli konut satış sözleşmeleri
- **Madde:** Madde 40 · **Başlık:** Ön ödemeli konut satış sözleşmeleri · **Fıkralar:** [1, 2, 3] · **Bentler:** None · **Parça:** 1/1 · **Sayfa:** [16]
- **Kısım/Bölüm:** Dördüncü Kısım: Tüketici Sözleşmeleri / Dördüncü Bölüm: Ön Ödemeli Konut Satışı
- **Değişiklik notları:** —

```text
(1) Ön ödemeli konut satış sözleşmesi, tüketicinin konut amaçlı bir taşınmazın satış bedelini önceden peşin veya taksitle ödemeyi, satıcının da bedelin tamamen veya kısmen ödenmesinden sonra taşınmazı tüketiciye devir veya teslim etmeyi üstlendiği sözleşmedir.
(2) Tüketicilere sözleşmenin kurulmasından en az bir gün önce, Bakanlıkça belirlenen hususları içeren ön bilgilendirme formu verilmek zorundadır.
(3) Yapı ruhsatı alınmadan, tüketicilerle ön ödemeli konut satış sözleşmesi yapılamaz.
```

### `TKHK-m57a-1`

- **Bağlam başlığı:** 6502 sayılı Tüketicinin Korunması Hakkında Kanun (TKHK) · Madde 57/A · Yenilenmiş ürünler
- **Madde:** Madde 57/A · **Başlık:** Yenilenmiş ürünler · **Fıkralar:** [1, 2, 3, 4, 5, 6] · **Bentler:** None · **Parça:** 1/1 · **Sayfa:** [28]
- **Kısım/Bölüm:** Beşinci Kısım: Tüketicinin Bilgilendirilmesi ve Menfaatlerinin Korunması / —
- **Değişiklik notları:** ['(Ek:24/3/2022-7392/9 md.)']

```text
(Ek:24/3/2022-7392/9 md.)
(1) Yenilenmiş ürünler; donanım, yazılım veya fiziki özelliklerinde iyileştirme yapılarak tekrar satışa sunulan kullanılmış mallardır.
(2) Yenilenmiş ürünlere tüketiciye teslim tarihinden itibaren asgari bir yıl garanti verilmesi zorunludur. Ancak özelliği nedeniyle bazı malların garanti şartları Bakanlıkça başka bir ölçü birimi ile de belirlenebilir.
(3) Yönetmelikle belirlenen mallar ancak Bakanlıkça yetkilendirilen merkezlerde yenilenmesi şartı ile yenilenmiş ürün olarak satılabilir.
(4) Yenileme merkezlerinin Bakanlıktan yetki belgesi alması zorunludur.
(5) Elektronik kimlik bilgisi bulunan malların kullanılmış ve kayıtlı olduğuna ilişkin doğrulama yapılmasının gerektiği durumda bu doğrulamalar Bakanlık, yenileme merkezi ve yetkili alıcı tarafından Bakanlıkça belirlenen usul ve esaslara göre Bilgi Teknolojileri ve İletişim Kurumu kayıtlarından yapılır.
(6) Hangi malların yenileme merkezleri tarafından yenileneceği, yenileme merkezlerinin kuruluşu ve sorumluluğu ile diğer uygulama usul ve esasları yönetmelikle belirlenir.
```

### `ETK-gecici2-1`

- **Bağlam başlığı:** 6563 sayılı Elektronik Ticaretin Düzenlenmesi Hakkında Kanun (ETK) · Geçici Madde 2 · İntibak süreci
- **Madde:** Geçici Madde 2 · **Başlık:** İntibak süreci · **Fıkralar:** [1, 2, 3, 4, 5, 6] · **Bentler:** None · **Parça:** 1/1 · **Sayfa:** [18]
- **Kısım/Bölüm:** — / —
- **Değişiklik notları:** ['(Ek:1/7/2022-7416/11 md.)', '(Ek:24/10/2024-7529/10 md.)', '(Ek:24/10/2024-7529/10 md.)']

```text
(Ek:1/7/2022-7416/11 md.)
(1) Bu maddeyi ihdas eden Kanunun yayımlandığı tarih itibarıyla;
a) Aracılık hizmeti sunduğu elektronik ticaret pazar yerlerinde kendisinin veya ekonomik bütünlük içinde bulunduğu kişilerin markasını taşıyan veya kullanım hakkını haiz olduğu malları satışa sunan veya satışına aracılık eden elektronik ticaret aracı hizmet sağlayıcılar, ek 2 nci maddenin birinci fıkrasının (a) bendinde,
b) 5411 sayılı Kanun kapsamında banka veya 6493 sayılı Kanun kapsamında elektronik para kuruluşu olarak yetkilendirilen işletmelerin ekonomik bütünlük içinde bulunduğu elektronik ticaret aracı hizmet sağlayıcılar, ek 2 nci maddenin dördüncü fıkrasının (a) ve (b) bentlerinde,
c) 4925 sayılı Kanun kapsamında eşya taşımacılığı faaliyetinde bulunan işletmeler, 655 sayılı Kanun Hükmünde Kararname kapsamında taşıma işleri organizatörü veya 6475 sayılı Kanun kapsamında posta hizmet sağlayıcı olarak yetkilendirilen işletmelerin ekonomik bütünlük içinde bulunduğu elektronik ticaret aracı hizmet sağlayıcılar, ek 2 nci maddenin dördüncü fıkrasının (c) bendinde,
yer alan yükümlülüklere 1/1/2024 tarihine kadar uyum sağlar.
(2) Bu maddeyi ihdas eden Kanunun yürürlüğe girdiği tarihten önce yapılan ve aynı tarihten itibaren altı ay içinde bu Kanuna uygun hâle getirilmeyen aracılık sözleşmelerinin ilgili hükümleri geçersizdir.
(3) Elektronik ticaret hizmet sağlayıcının ek 3 üncü, elektronik ticaret aracı hizmet sağlayıcının ek 4 üncü madde kapsamındaki lisans alma yükümlülüğü 1/1/2025 tarihinden itibaren yerine getirilir.
(4) Ek 2 nci, ek 3 üncü ve ek 4 üncü maddelerde belirtilen eşikler, 2023 yılının Şubat ayı içinde Cumhurbaşkanı tarafından yarısına kadar artırılabilir.
(5) (Ek:24/10/2024-7529/10 md.) 2024 yılına ilişkin lisans ücretinin hesaplanmasında, ek 4 üncü maddenin yedinci fıkrasının (b) bendinin alt bentlerinde belirtilen tutarların dört katı elektronik ticaret aracı hizmet sağlayıcının net işlem hacminden indirilir.
(6) (Ek:24/10/2024-7529/10 md.) 2025 yılına ilişkin lisans ücretinin hesaplanmasında, ek 4 üncü maddenin yedinci fıkrasının (b) bendinin alt bentlerinde belirtilen tutarların üç katı elektronik ticaret aracı hizmet sağlayıcının net işlem hacminden indirilir.
```

### `ETK-m6-1`

- **Bağlam başlığı:** 6563 sayılı Elektronik Ticaretin Düzenlenmesi Hakkında Kanun (ETK) · Madde 6 · Ticari elektronik ileti gönderme şartı
- **Madde:** Madde 6 · **Başlık:** Ticari elektronik ileti gönderme şartı · **Fıkralar:** [1, 2] · **Bentler:** None · **Parça:** 1/1 · **Sayfa:** [4]
- **Kısım/Bölüm:** — / —
- **Değişiklik notları:** —

```text
(1) Ticari elektronik iletiler, alıcılara ancak önceden onayları alınmak kaydıyla gönderilebilir. Bu onay, yazılı olarak veya her türlü elektronik iletişim araçlarıyla alınabilir. Kendisiyle iletişime geçilmesi amacıyla alıcının iletişim bilgilerini vermesi hâlinde, temin edilen mal veya hizmetlere ilişkin değişiklik, kullanım ve bakıma yönelik ticari elektronik iletiler için ayrıca onay alınmaz.
(2) Esnaf ve tacirlere önceden onay alınmaksızın ticari elektronik iletiler gönderilebilir.
```

### `ETK-m12-2`

- **Bağlam başlığı:** 6563 sayılı Elektronik Ticaretin Düzenlenmesi Hakkında Kanun (ETK) · Madde 12 · Cezai hükümler · fıkra 1 (h, ı, i, j, k, l, m, n, o, ö, p bentleri)
- **Madde:** Madde 12 · **Başlık:** Cezai hükümler · **Fıkralar:** [1] · **Bentler:** ['h', 'ı', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'ö', 'p'] · **Parça:** 2/5 · **Sayfa:** [6, 7, 8]
- **Kısım/Bölüm:** — / —
- **Değişiklik notları:** ['(Değişik:1/7/2022-7416/6 md.)']
- **Dipnot 4** (degisiklik_gecmisi, madde başlığı): 1/7/2022 tarihli ve 7416 sayılı Kanunun 6 ncı maddesiyle bu maddeye ikinci fıkrasından sonra gelmek üzere fıkralar eklenmiş ve mevcut üçüncü fıkra buna göre teselsül ettirilmiştir.
- **Dipnot 5** (tablo_atfi, madde başlığı): Bu maddedeki 1/1/2026 ile 31/12/2026 tarihleri arasında uygulanacak idari para cezası tutarları ile ilgili olarak Kanunun sonundaki tabloya bakınız.

```text
(1) (Değişik:1/7/2022-7416/6 md.) Bu Kanunun; […]
h) Ek 1 inci maddesinin ikinci fıkrasının (b) bendine ve ek 2 nci maddesinin ikinci fıkrasının (b) bendine aykırı hareket eden elektronik ticaret aracı hizmet sağlayıcıya, her bir elektronik ticaret hizmet sağlayıcı için beş yüz bin Türk lirası,
ı) Ek 1 inci maddesinin ikinci fıkrasının (c) bendine aykırı hareket eden ve Bakanlık tarafından yapılan uyarıya rağmen aykırılığı ortadan kaldırmayan elektronik ticaret aracı hizmet sağlayıcıya, her bir aykırılık için on bin Türk lirası,
i) Ek 1 inci maddesinin ikinci fıkrasının (d) bendine aykırı hareket eden elektronik ticaret aracı hizmet sağlayıcıya, haksız olarak alınan bedelin on katı,
j) Ek 1 inci maddesinin ikinci fıkrasının (e) bendine aykırı hareket eden elektronik ticaret aracı hizmet sağlayıcıya, haksız uygulamada bulunulan her bir elektronik ticaret hizmet sağlayıcı için üç yüz bin Türk lirası,
k) Ek 2 nci maddesinin birinci fıkrasının (a) bendine aykırı hareket eden elektronik ticaret aracı hizmet sağlayıcıya, aykırılığın gerçekleştiği tarihten bir önceki takvim yılına ait net satış tutarının yüzde beşi oranında,
l) Ek 2 nci maddesinin birinci fıkrasının (b) bendi ile ikinci fıkrasının (f) bendine aykırı hareket eden elektronik ticaret aracı hizmet sağlayıcıya, yüz bin Türk lirasından az olmamak üzere, aykırılığın gerçekleştiği tarihten bir önceki takvim yılına ait net satış tutarının on binde beşi oranında,
m) Ek 2 nci maddesinin birinci fıkrasının (ç) bendine aykırı hareket eden elektronik ticaret aracı hizmet sağlayıcıya, her bir aykırılık için on bin Türk lirası,
n) Ek 2 nci maddesinin ikinci fıkrasının (a) bendine aykırı hareket eden elektronik ticaret aracı hizmet sağlayıcıya, aykırılığın gerçekleştiği tarihten bir önceki takvim yılına ait net satış tutarının yüzde onuna kadar,
o) Ek 2 nci maddesinin ikinci fıkrasının (c) bendine aykırı hareket eden elektronik ticaret aracı hizmet sağlayıcı ve elektronik ticaret hizmet sağlayıcıya on milyon Türk lirası,
ö) Ek 2 nci maddesinin ikinci fıkrasının (ç) ve (d) bentlerine aykırı hareket eden elektronik ticaret aracı hizmet sağlayıcıya ve elektronik ticaret hizmet sağlayıcıya süresi içinde yapılmayan her bir bildirim için bir milyon Türk lirası,
p) Ek 2 nci maddesinin ikinci fıkrasının (e) bendine aykırı hareket eden elektronik ticaret aracı hizmet sağlayıcı ve elektronik ticaret hizmet sağlayıcıya bir milyon Türk lirası,
```

### `KVKK-gecici3-1`

- **Bağlam başlığı:** 6698 sayılı Kişisel Verilerin Korunması Kanunu (KVKK) · Geçici Madde 3
- **Madde:** Geçici Madde 3 · **Başlık:** None · **Fıkralar:** [1, 2] · **Bentler:** None · **Parça:** 1/1 · **Sayfa:** [19]
- **Kısım/Bölüm:** — / Yedinci Bölüm: Çeşitli Hükümler
- **Değişiklik notları:** ['(Ek:2/3/2024-7499/36 md.)']

```text
(Ek:2/3/2024-7499/36 md.)
(1) 9 uncu maddenin bu maddeyi ihdas eden Kanunla değiştirilmeden önceki birinci fıkrası, maddenin yürürlüğe giren değişik haliyle birlikte 1/9/2024 tarihine kadar uygulanmaya devam olunur.
(2) 1/6/2024 tarihi itibarıyla sulh ceza hâkimliklerinde görülmekte olan başvurular, bu hâkimliklerce görülmeye devam olunur.
```

### `KVKK-m32-1`

- **Bağlam başlığı:** 6698 sayılı Kişisel Verilerin Korunması Kanunu (KVKK) · Madde 32 · Yürürlük
- **Madde:** Madde 32 · **Başlık:** Yürürlük · **Fıkralar:** [1] · **Bentler:** None · **Parça:** 1/1 · **Sayfa:** [19]
- **Kısım/Bölüm:** — / Yedinci Bölüm: Çeşitli Hükümler
- **Değişiklik notları:** —

```text
(1) Bu Kanunun;
a) 8 inci, 9 uncu, 11 inci, 13 üncü, 14 üncü, 15 inci, 16 ncı, 17 nci ve 18 inci maddeleri yayımı tarihinden altı ay sonra,
b) Diğer maddeleri ise yayımı tarihinde,
yürürlüğe girer.
```

### `KVKK-m31-1`

- **Bağlam başlığı:** 6698 sayılı Kişisel Verilerin Korunması Kanunu (KVKK) · Madde 31 · Yönetmelik
- **Madde:** Madde 31 · **Başlık:** Yönetmelik · **Fıkralar:** [1] · **Bentler:** None · **Parça:** 1/1 · **Sayfa:** [18]
- **Kısım/Bölüm:** — / Yedinci Bölüm: Çeşitli Hükümler
- **Değişiklik notları:** —

```text
(1) Bu Kanunun uygulanmasına ilişkin yönetmelikler Kurum tarafından yürürlüğe konulur.
```

### `MSY-m11-1`

- **Bağlam başlığı:** Mesafeli Sözleşmeler Yönetmeliği (MSY) · Madde 11 · Cayma hakkının kullanımı
- **Madde:** Madde 11 · **Başlık:** Cayma hakkının kullanımı · **Fıkralar:** [1, 2, 3, 4, 5] · **Bentler:** None · **Parça:** 1/1 · **Sayfa:** [4, 5]
- **Kısım/Bölüm:** — / Üçüncü Bölüm: Cayma Hakkının Kullanımı ve Tarafların Yükümlülükleri
- **Değişiklik notları:** ['(Değişik ibare:RG-23/8/2022-31932)', '(Ek:RG-23/8/2022-31932)']
- **Dipnot 1** (yururluk, fıkra 1): Bu değişiklik 1/10/2022 tarihinde yürürlüğe girer.

```text
(1) Cayma hakkının kullanıldığına dair bildirimin cayma hakkı süresi dolmadan, yazılı olarak veya kalıcı veri saklayıcısı ile (Değişik ibare:RG-23/8/2022-31932) satıcı, sağlayıcı veya aracı hizmet sağlayıcıya yöneltilmesi yeterlidir.
(2) Cayma hakkının kullanılmasında tüketici, EK’te yer alan formu kullanabileceği gibi cayma kararını bildiren açık bir beyanda da bulunabilir. Satıcı veya sağlayıcı, tüketicinin bu formu doldurabilmesi veya cayma beyanını gönderebilmesi için internet sitesi üzerinden seçenek de sunabilir. İnternet sitesi üzerinden tüketicilere cayma hakkı sunulması durumunda satıcı veya sağlayıcı, tüketicilerin iletmiş olduğu cayma taleplerinin kendilerine ulaştığına ilişkin teyit bilgisini tüketiciye derhal iletmek zorundadır.
(3) Sesli iletişim yoluyla yapılan satışlarda, satıcı veya sağlayıcı, EK’te yer alan formu en geç mal teslimine veya hizmet ifasına kadar tüketiciye göndermek zorundadır. Tüketici bu tür satışlarda da cayma hakkını kullanmak için bu formu kullanabileceği gibi, ikinci fıkradaki yöntemleri de kullanabilir.
(4) Bu maddede geçen cayma hakkının kullanımına ilişkin ispat yükümlülüğü tüketiciye aittir.
(5) (Ek:RG-23/8/2022-31932) Platform üzerinden kurulan mesafeli sözleşmelerde aracı hizmet sağlayıcı tüketicinin EK’te yer alan formu doldurabilmesi veya cayma beyanını gönderebilmesi için platform üzerinde gerekli sistemi kurmak ve tüketicilerin iletmiş olduğu cayma beyanlarının kendisine ve satıcı veya sağlayıcıya ulaştığına ilişkin teyit bilgisini tüketiciye derhal iletmek zorundadır.
```

### `MSY-m20-1`

- **Bağlam başlığı:** Mesafeli Sözleşmeler Yönetmeliği (MSY) · Madde 20 · Bilgilerin saklanması ve ispat yükümlülüğü
- **Madde:** Madde 20 · **Başlık:** Bilgilerin saklanması ve ispat yükümlülüğü · **Fıkralar:** [1, 2, 3] · **Bentler:** None · **Parça:** 1/1 · **Sayfa:** [8]
- **Kısım/Bölüm:** — / Dördüncü Bölüm: Diğer Hükümler
- **Değişiklik notları:** ['(Değişik cümle:RG-23/8/2022-31932)', '(Ek cümle:RG-9/2/2019-30681)']
- **Dipnot 1** (yururluk, fıkra 2): Bu değişiklik 1/10/2022 tarihinde yürürlüğe girer.

```text
(1) Satıcı veya sağlayıcı, bu Yönetmelik kapsamında düzenlenen cayma hakkı, bilgilendirme, teslimat ve diğer hususlardaki yükümlülüklerine dair her bir işleme ilişkin bilgi ve belgeyi üç yıl boyunca saklamak zorundadır.
(2) (Değişik cümle:RG-23/8/2022-31932)Aracı hizmet sağlayıcı, bu Yönetmelikte yer alan hususlardan dolayı satıcı veya sağlayıcı ile yapılan işlemlere ilişkin kayıtları üç yıl boyunca tutmak ve istenilmesi halinde bu bilgileri ilgili kurum, kuruluş ve tüketicilere vermekle yükümlüdür. (Ek cümle:RG-9/2/2019-30681) Ancak abonelik sözleşmesinin kamu hizmetlerinin tek noktadan sunulduğu ortak kamu elektronik platformu üzerinden kurulması halinde, kayıtların tutulması ve bilgilerin sunulmasına ilişkin yükümlülük satıcı veya sağlayıcıya aittir.
(3) Satıcı veya sağlayıcı elektronik ortamda tüketiciye teslim edilen gayrimaddi malların veya ifa edilen hizmetlerin ayıpsız olduğunu ispatla yükümlüdür.
```

### `MSY-m13-1`

- **Bağlam başlığı:** Mesafeli Sözleşmeler Yönetmeliği (MSY) · Madde 13 · Tüketicinin yükümlülükleri
- **Madde:** Madde 13 · **Başlık:** Tüketicinin yükümlülükleri · **Fıkralar:** [1, 2, 3] · **Bentler:** None · **Parça:** 1/1 · **Sayfa:** [6, 7]
- **Kısım/Bölüm:** — / Üçüncü Bölüm: Cayma Hakkının Kullanımı ve Tarafların Yükümlülükleri
- **Değişiklik notları:** ['(Ek ibare:RG-23/8/2022-31932)', '(Ek:RG-23/8/2022-31932)', '(Mülga:RG-24/5/2025-32909)']
- **Dipnot 2** (yururluk, fıkra 1): 14/9/2022 tarihli ve 31953 sayılı Resmî Gazete’de yayımlanan Yönetmelik uyarınca 23/8/2022 tarihli ve 31932 sayılı Resmî Gazete’de yayımlanan değişiklikle Yönetmeliğin 5 inci maddesinin birinci fıkrasının (g) bendi, 12 nci maddesi, 12/A maddesinin yedinci fıkrasının (b) bendi, 13 üncü maddesinin bir…
- **Dipnot 4** (yururluk, fıkra 3): Bu değişiklik 1/1/2026 tarihinde yürürlüğe girer.

```text
(1) Satıcı veya sağlayıcı malı kendisinin geri alacağına dair bir teklifte bulunmadıkça, tüketici cayma hakkını kullandığına ilişkin bildirimi yönelttiği tarihten itibaren on (Ek ibare:RG-23/8/2022-31932)dört gün içinde malı satıcı veya sağlayıcıya ya da yetkilendirmiş olduğu kişiye geri göndermek zorundadır.
(2) Tüketici, cayma süresi içinde malı, işleyişine, teknik özelliklerine ve kullanım talimatlarına uygun bir şekilde kullandığı takdirde meydana gelen değişiklik ve bozulmalardan sorumlu değildir.
(3) (Ek:RG-23/8/2022-31932)(Mülga:RG-24/5/2025-32909)
```

