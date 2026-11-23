# Arama teşhisi: iki geliştirme seti

`python scripts/diagnose_retrieval.py --runs 3` ile ölçüldü. Ham veri `evals/teshis/sonuclar.json`,
bağlam düzeyi `evals/teshis/baglam_duzeyi.json`. **Hiçbir arama ayarı değiştirilmedi.**

- Geliştirme seti 1 (dev1): `evals/retrieval.yaml`, 26 cevaplı soru, alan `dogru`.
- Geliştirme seti 2 (dev2): `evals/answers.yaml`, 15 cevaplı soru, alan `dayanak`.
- Ölçüt **@8**: her dayanak gereksinimi ilk 8 parçadan birinin maddesiyle karşılanıyor mu.
  Parça düzeyinde ölçülüyor, çünkü bağlama giden birim parça.
- **Bağlam düzeyi:** Aynı ilk 8 parçadan `context.kur` ile kurulan bağlam. 1. düzeltmeden sonra
  ceza tablosu ve bağlı madde eklemeleri buna dahil.
- **Yeniden yazım:** Haiku 5.5, prompt v3, her koşuda soru başına bir kez. İki "+ yeniden yazım"
  yapılandırması aynı sorguları kullandı.
- **Sayı denetimi** 366 üretilen sorgudan hiçbirini atmadı (dev1 230, dev2 136).

## a) Yan yana sonuç (3 koşu; en düşük / medyan / en yüksek)

| Yapılandırma | dev1 arama @8 (26) | dev1 bağlam (26) | dev2 arama @8 (15) | dev2 bağlam (15) |
|---|---|---|---|---|
| **BM25 + yeniden yazım** (varsayılan) | 24 / 24 / 25 | 24 / 24 / 25 | **10 / 10 / 11** | 12 / 12 / 12 |
| bge-m3 hibrit + yeniden yazım | 24 / 25 / 26 | 24 / 25 / 26 | 11 / 11 / 11 | 12 / 12 / 13 |
| yalnız bge-m3 | 23 | 23 | **13** | 13 |
| düz BM25 | 19 | 19 | **12** | 13 |

(Yalnız bge-m3 ve düz BM25 model çağrısı yapmaz, üç koşuda da aynıdır.)

- **dev1'de** yeniden yazım düz BM25'e göre +5–6 soru kazandırıyor.
- **dev2'de** varsayılan hat düz BM25'ten kötü: arama düzeyinde 10–11'e karşı 12, bağlam düzeyinde
  12'ye karşı 13. En iyisi yalnız bge-m3 (13).
- 1. düzeltme (tablo atfı) dev2'de iki ceza sorusunu (A14, A15) bağlam düzeyinde kurtarıyor. Bu
  yüzden bağlam sütunu arama sütunundan yüksek. dev1'de ceza sorusu yok, iki sütun aynı.

## b) Kaçan sorular

Varsayılan hat (BM25 + yeniden yazım). Sıra = doğru maddenin ilk parçasının sırası (koşu 1 / 2 / 3).

Kategoriler:
- **kelime uyuşmazlığı**
- **yanlış kavrama çevirme:** Yeniden yazım soruyu başka bir hukuki kavrama taşıyor.
- **benzer madde kalabalığı**
- **parça bölünmesi:** Aynı maddenin birçok parçası ilk 8'i dolduruyor.
- **sayı denetimi:** Hiçbir soruda görülmedi.
- **RRF seyreltmesi:** Senin listende yoktu; veride açıkça görüldüğü için ekledim. Özgün soru doğru
  maddeyi zaten üstte buluyor, ama 3–4 yeniden yazılmış sorgunun sıralamaları ağırlıksız
  birleşimde onu aşağı itiyor.

### dev2

| Soru | Doğru madde | Varsayılan sıra | Düz BM25 | Yalnız bge-m3 | Neden |
|---|---|---|---|---|---|
| A07 pazaryeri satıcıya ödeme süresi | ETK Ek 1 | 16 / 12 / 13 | 28 | 134 | **yanlış kavrama çevirme** + kelime uyuşmazlığı |
| A10 sağlık verisi + Kurula şikâyet süresi | KVKK 6 + 14 | 6: 9/4/9 · 14: 21/13/19 | 6: **7** · 14: **1** ✓ | 6: 13 · 14: 1 | **RRF seyreltmesi** + benzer madde kalabalığı |
| A11 satışa bağlı diğer sözleşmeler | MSY 14 | 21 / 17 / 30 | 129 | **5** ✓ | **yanlış kavrama çevirme** |
| A14 sipariş teyidi cezası 2026 | ETK tablo + m.12/4 | tablo: 11/16/8 | tablo: **3** ✓ | tablo: 1 ✓ | parça bölünmesi + benzer madde kalabalığı (bağlamda ✓, 1. düzeltme) |
| A15 yetkisiz kapıdan satış cezası 2026 | TKHK tablo + m.77 | tablo: 18/31/21 | tablo: 15 | tablo: 1 ✓ | **parça bölünmesi** (bağlamda ✓, 1. düzeltme) |

- **A07.** Üretilen sorgular: "pazaryeri aracı hizmet sağlayıcı satıcıya ödeme yükümlülüğü", "elektronik
  ticaret aracı hizmet sağlayıcı satış bedelinin ödenmesi süresi", "mesafeli satış bedelinin satıcıya
  aktarılması". Madde bu durumu bir ödeme yükümlülüğü olarak değil, *haksız ticari uygulama* olarak
  tanımlıyor. Bu kavrama hiçbir yöntem ulaşamıyor. Üçüncü sorgu konuyu tüketici tarafındaki mesafeli
  satışa kaydırıyor. Soru satıcının (B2B) bakış açısından ve dört yöntemin hepsinde kaçıyor; zor bir soru.
- **A10.** Düz BM25 her iki maddeyi ilk 8'de buluyor (14. madde 1. sırada). Yeniden yazılmış üç sorgu
  "veri sorumlusuna başvuru", "Kurula şikâyet süresi", "özel nitelikli veri" diyor. KVKK m.13
  (başvuru), m.15 (şikâyet üzerine inceleme), m.16 ve m.22 (Kurul) bu kelimelerle dolu olduğu için
  birleşimde öne çıkıyor; m.14 13.–21. sıraya düşüyor. Kaybın nedeni sorguların yanlışlığı değil,
  aynı ağırlıkla birleştirilmeleri.
- **A11.** Üç koşunun hepsinde sorgular "satışa bağlı diğer sözleşmeler" ifadesini "**bağlı kredi
  sözleşmesi**"ne (TKHK m.30–31) çeviriyor; doğru kavram MSY m.14'teki "**yan sözleşme**". Yalnız
  bge-m3 anlamca yakın olduğu için 5. sırada buluyor.
- **A14 ve A15.** TKHK m.77'nin 7, ETK m.12'nin 5 parçası var. Yeniden yazılmış "idari para cezası"
  sorguları bu parçalarla (A14'te üstelik yanlış kanunun 77. maddesiyle) ilk 8'i dolduruyor, tablo
  dışarıda kalıyor. 1. düzeltmeden sonra bu parçaların tablo atfı tabloyu bağlama ekliyor; bağlam
  düzeyinde ikisi de üç koşuda ✓.

### dev1

| Soru | Doğru madde | Varsayılan sıra | Düz BM25 | Yalnız bge-m3 | Neden |
|---|---|---|---|---|---|
| S06 cayma hakkının kullanılamayacağı sözleşmeler | MSY 15 | 22 / 12 / 22 | 24 | **1** | benzer madde kalabalığı (cayma hakkı 6+ maddede) + RRF seyreltmesi |
| S15 üye getirdikçe kazanç (piramit) | TKHK 80 | 3 / **27** / 2 | **1** | 1 | **RRF seyreltmesi** + yanlış kavrama çevirme (koşu 2: "haksız ticari uygulama", "aldatıcı" → TKHK 62) |
| S17 garantide onarılan ürün tekrar bozulursa | TKHK 56 + 11 | 56: 3/1/**9** | 1 / 5 | 5 / 2 | benzer madde kalabalığı (ayıplı mal maddeleri); yalnız koşu 3'te |

S06'da sorgulardan biri maddenin başlığını neredeyse aynen içeriyor ("cayma hakkı istisnaları"). Buna
rağmen "cayma hakkı" geçen diğer sorgular TKHK m.18, 24, 43, 48 ve 50'yi öne taşıyor.

### Nedenlerin dağılımı (varsayılan hatta kaçanlar; dev1 3 + dev2 5 soru)

| Neden | Ana neden olduğu soru | Yeniden yazım kaynaklı mı? |
|---|---|---|
| RRF seyreltmesi | A10, S15 (+ S06, A14'te ikincil) | Evet: düz BM25 bu soruları buluyor |
| Yanlış kavrama çevirme | A07, A11 | Evet |
| Parça bölünmesi | A14, A15 (bağlamda düzeldi) | Kısmen: yeniden yazım kalabalığı artırıyor |
| Benzer madde kalabalığı | S06, S17 | Kısmen |
| Kelime uyuşmazlığı | A07 (ikincil) | Hayır (yeniden yazımın çözmesi gereken sorun) |
| Sayı denetiminin attığı sorgu | — | Hiç görülmedi |

## c) İki set arasındaki farkın nedeni hakkında görüşüm

Bence iki etki birlikte çalışıyor; ikincisi daha önemli.

1. **dev2 bazı yönlerden yapısal olarak daha zor.**
   - İki ceza sorusu tablo gerektiriyor ve tablolar çok parçalı maddelerin gölgesinde kalıyor.
   - A07 satıcının (B2B) bakış açısından ve kavram sıçraması istiyor ("ödeme süresi" → "haksız
     ticari uygulama").
   - A11 ince bir kavram ayrımı ("yan sözleşme" ile "bağlı kredi") istiyor.
   - dev1'de bu türden yalnızca S06 ve S17 vardı.

   Ama bu tek başına açıklama değil: dev2'de **düz BM25 varsayılan hattan daha iyi** (12'ye karşı
   10–11). Sorular yalnızca zor olsaydı yeniden yazımın en azından zarar vermemesi gerekirdi.

2. **Seçim ve ayar dev1'e göre yapıldı; dev2'de tutmadı.**
   - BM25 + yeniden yazım dev1'deki sonuçlara bakılarak seçildi.
   - Prompt v2'nin kuralı ("her alt soru için bir sorgu") dev1'deki S21 hatasından türedi.
   - Model seçimi de dev1 koşularıyla yapıldı.

   Prompt'taki örnekler uydurma olduğu için bu klasik anlamda bir veri sızıntısı değil; ama
   **seçim yanlılığı** var. dev1'de yeniden yazımın kazandırdığı sorular ağırlıkla günlük dildeki
   sorulardı (kelime uyuşmazlığı). dev2'nin cevaplı sorularının yarısından fazlası ise zaten madde
   diline yakın. Orada özgün sorgu çoğunlukla yeterli ve yeniden yazım ağırlıksız RRF yüzünden
   yalnızca seyreltme yapıyor. Aynı mekanizma dev1'de de var (S15, S06), ama kazançların arkasında
   saklanıyordu.

   Sayılarla, dev2'de yeniden yazım düz BM25'e göre doğru maddeyi:
   - 3 soruda yukarı taşıyor: A09 (5 → 2); A07 (28 → 12–16) ve A11 (129 → 17–30), ama bu ikisi yine
     ilk 8'e giremiyor.
   - 4 soruda belirgin biçimde aşağı itiyor: A04 (1 → 4), A10 (m.14: 1 → 13–21), A14 (tablo: 3 → 8–16),
     A15 (tablo: 15 → 18–31).
   - 2 soruda bir sıra aşağı itiyor: A12 ve A13 (1 → 2).

   dev1'de net kazanç +5–6.

3. **Örneklem küçük.** dev2'de bir soru yaklaşık 7 puan, dev1'de yaklaşık 4 puan. Yine de dev2'deki ters
   işaret üç koşuda da aynı ve mekanizma soru soru izlenebiliyor. Bu yüzden gürültü olduğunu
   düşünmüyorum.

## Öneriler (öncelik sırasıyla; hiçbiri uygulanmadı)

1. **Özgün sorgunun ağırlığını artırmak.** Bulguların en çok tekrarlanan mekanizması (A10, S15, S06,
   A14) ağırlıksız RRF'te özgün sorgunun 3–4 listeden yalnızca biri olması. Seçenekler:
   - Yeniden yazılmış sorguların sıralamalarını önce kendi aralarında birleştirip, sonucu özgün
     sorguyla 1:1 birleştirmek (iki aşamalı RRF).
   - Özgün sorguya sabit bir ağırlık vermek.

   Her iki sette de, aynı koşularla ölçülmeli. Beklentim: dev2'de A10 geri gelir, dev1'de günlük dil
   kazançlarının çoğu korunur.
2. **Parça çeşitliliği.** İlk 8'e aynı maddeden en fazla 2 parça almak. TKHK m.77 (7 parça) ve ETK m.12
   (5 parça) ilk 8'i doldurmasın. A14 ve A15 bağlamda 1. düzeltmeyle zaten çözüldü; bu öneri aynı sorunun
   tablo dışı türlerini (ör. çok parçalı tanımlar ve yükümlülük maddeleri) hedefliyor. Etkisi her iki sette ölçülmeli.
3. **Yeniden yazım prompt'unda özgün ifadeyi koruma.** Sorgulardan birinin kullanıcının kendi
   kelimelerini (ör. "yan sözleşme", "diğer sözleşmeler") korumasını istemek. A11 gibi yanlış kavram
   çevirmelerinin zararını sınırlar. Prompt'a belirli bir hukuki kavramı (ör. "yan sözleşme") örnek
   olarak eklemeyi **önermiyorum**: bu, dev2'deki tek bir soruya ayar yapmak olur.
4. **Değerlendirme setlerini büyütmek.** Her türden (günlük dil, iki madde, ceza, kavram ayrımı) en az
   5–8 soru olmalı. Şu an tek soru dev2'de 7 puan. Bir sonraki seçim kararından önce yapılmalı.
5. **Yoğun aramayı yeniden değerlendirmek, sonra.** Yalnız bge-m3 dev2'de en iyisi (13), dev1'de
   yeniden yazımlı hatların gerisinde (23). Hiçbir yöntem iki sette birden en iyi değil. Bellek kısıtı
   (1,9 GB) da sürüyor. Önce 1. ve 2. öneriler ölçülmeli; yoğun arama ancak onlar yetmezse yeniden açılmalı.

**Holdout:** İki geliştirme seti de artık seçim için kullanıldı. Hangi öneri uygulanırsa uygulansın,
son karar ancak senin yazacağın holdout setinde, tek yapılandırmayla ve önceden kaydedilmiş bir kuralla
doğrulanmalı.
