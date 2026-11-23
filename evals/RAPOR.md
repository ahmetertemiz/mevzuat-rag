# Arama değerlendirme raporu

`python scripts/eval_retrieval.py` tarafından üretilir. Soru seti: `evals/retrieval.yaml` (25 soru: 7 madde dili, 8 günlük dil, 6 i̇ki madde, 4 cevapsız).

**Bu sonuçlara göre hiçbir ayar yapılmadı.** Model, parça sınırı, tokenizer, durak kelimeler ve RRF sabiti sorular yazılmadan önce belirlendi.

Ölçüt: doğru madde, maddeye indirgenmiş sonuç listesinin ilk 1 / 3 / 5'inde mi. İki maddeli sorularda genel tabloda iki gereksinimin de karşılanması ("tümü") aranır.

## 1. Genel sonuç (cevaplı 21 soru)

| Yöntem | @1 | @3 | @5 |
|---|---|---|---|
| Hibrit (RRF) | 8/21 (38%) | 17/21 (81%) | 17/21 (81%) |
| Yalnız embedding | 12/21 (57%) | 18/21 (86%) | 20/21 (95%) |
| Yalnız BM25 | 6/21 (29%) | 10/21 (48%) | 13/21 (62%) |

## 2. Soru türüne göre

### Madde dili

| Yöntem | @1 | @3 | @5 |
|---|---|---|---|
| Hibrit (RRF) | 6/7 (86%) | 6/7 (86%) | 6/7 (86%) |
| Yalnız embedding | 7/7 (100%) | 7/7 (100%) | 7/7 (100%) |
| Yalnız BM25 | 5/7 (71%) | 6/7 (86%) | 6/7 (86%) |

### Günlük dil

| Yöntem | @1 | @3 | @5 |
|---|---|---|---|
| Hibrit (RRF) | 2/8 (25%) | 7/8 (88%) | 7/8 (88%) |
| Yalnız embedding | 5/8 (62%) | 7/8 (88%) | 7/8 (88%) |
| Yalnız BM25 | 1/8 (12%) | 2/8 (25%) | 3/8 (38%) |

### İki madde

| Yöntem | tümü @1 | tümü @3 | tümü @5 | en az biri @1 | en az biri @3 | en az biri @5 |
|---|---|---|---|---|---|---|
| Hibrit (RRF) | 0/6 (0%) | 4/6 (67%) | 4/6 (67%) | 4/6 (67%) | 6/6 (100%) | 6/6 (100%) |
| Yalnız embedding | 0/6 (0%) | 4/6 (67%) | 6/6 (100%) | 4/6 (67%) | 6/6 (100%) | 6/6 (100%) |
| Yalnız BM25 | 0/6 (0%) | 2/6 (33%) | 4/6 (67%) | 3/6 (50%) | 6/6 (100%) | 6/6 (100%) |

*İki madde, @1:* tek sonuçta iki ayrı madde bulunamayacağı için "tümü @1" bu türde tanım gereği 0'dır.

## 3. Cevabı olmayan sorular

İsabet ölçülemez. İlk sonucun skoru, cevaplı soruların ilk sonuç skorlarıyla karşılaştırıldı. Skor ölçekleri yöntemler arasında farklıdır (embedding: kosinüs, BM25: ham skor, hibrit: RRF).

| Yöntem | Cevaplı sorularda ilk skor (en düşük / medyan) | S22 | S23 | S24 | S25 |
|---|---|---|---|---|---|
| Hibrit (RRF) | 0.031 / 0.033 | 0.033 | 0.031 | 0.033 | 0.033 |
| Yalnız embedding | 0.546 / 0.679 | 0.573 | 0.541 | 0.577 | 0.630 |
| Yalnız BM25 | 7.132 / 14.310 | 8.411 | 10.690 | 10.312 | 6.264 |

- Hibrit (RRF): cevapsız soruların 0/4 tanesinin ilk skoru, cevaplı soruların en düşük ilk skorunun altında.
- Yalnız embedding: cevapsız soruların 1/4 tanesinin ilk skoru, cevaplı soruların en düşük ilk skorunun altında.
- Yalnız BM25: cevapsız soruların 1/4 tanesinin ilk skoru, cevaplı soruların en düşük ilk skorunun altında.

Cevapsız soruların ilk sonuçları (hibrit):

- **S22** "Kiracının depozitosunu ev sahibi ne zaman iade etmek zorundadır?" → `MSY:12`, `TKHK:45`, `MSY:16`
- **S23** "İnternetten yapılan satışlarda KDV oranı yüzde kaç uygulanır?" → `ETK:12`, `ETK:Ek 2`, `ETK:Ek 3`
- **S24** "İşten çıkarılan bir çalışanın kıdem tazminatı nasıl hesaplanır?" → `KVKK:27`, `TKHK:37`, `KVKK:23`
- **S25** "Trafik cezasına itiraz süresi kaç gündür?" → `ETK:12`, `TKHK:77/A`, `TKHK:77`

## 4. Soru bazında sonuçlar

Hücrelerde doğru maddenin (her gereksinim için) maddeye indirgenmiş listedeki sırası. `—` ilk 5'te yok anlamına gelir; parantez içinde tam sıra.

| Soru | Tür | Doğru | Hibrit (RRF) | Yalnız embedding | Yalnız BM25 |
|---|---|---|---|---|---|
| S01 | Madde dili | MSY:9/TKHK:48 | 1 | 1 | 2 |
| S02 | Madde dili | TKHK:11 | 1 | 1 | 1 |
| S03 | Madde dili | TKHK:12 | 1 | 1 | 1 |
| S04 | Madde dili | ETK:6 | 1 | 1 | 1 |
| S05 | Madde dili | KVKK:11 | 1 | 1 | 1 |
| S06 | Madde dili | MSY:15 | — (12) | 1 | — (21) |
| S07 | Madde dili | TKHK:18 | 1 | 1 | 1 |
| S08 | Günlük dil | MSY:9/TKHK:48 | — (16) | — (24) | 2 |
| S09 | Günlük dil | TKHK:10 | 3 | 1 | — (20) |
| S10 | Günlük dil | MSY:16/TKHK:48 | 1 | 1 | 5 |
| S11 | Günlük dil | TKHK:7 | 2 | 2 | — (15) |
| S12 | Günlük dil | TKHK:6 | 2 | 1 | — (6) |
| S13 | Günlük dil | ETK:8 | 3 | 2 | — (15) |
| S14 | Günlük dil | KVKK:13 | 3 | 1 | — (15) |
| S15 | Günlük dil | TKHK:80 | 1 | 1 | 1 |
| S16 | İki madde | MSY:13 + MSY:12 | 1, 3 | 1, 2 | 2, 5 |
| S17 | İki madde | TKHK:56 + TKHK:11 | 1, 3 | 5, 2 | 1, 5 |
| S18 | İki madde | TKHK:68 + TKHK:73/A | 2, 1 | 2, 1 | 2, 1 |
| S19 | İki madde | MSY:17 + MSY:16/TKHK:48 | — (7), 2 | 2, 4 | — (18), 2 |
| S20 | İki madde | MSY:5 + MSY:7 | — (8), 2 | 3, 1 | — (10), 2 |
| S21 | İki madde | KVKK:11/KVKK:7 + KVKK:13 | 1, 2 | 1, 3 | 1, 2 |

## 5. Başarısız sorular ve nedenleri

Başarısız: ilgili yöntemde doğru madde(ler) ilk 5'te yok (iki maddeli sorularda: iki gereksinimden en az biri yok). Nedenler sonuçlara bakılarak elle sınıflandırıldı (`evals/siniflandirma.yaml`).

Kategoriler:

- `kelime_uyusmazligi`: Soru ile madde farklı kelimeler kullanıyor (kargo/taşıyıcı, kampanya mesajı/ticari elektronik ileti, kanıtlamak/ispat). BM25'in yapısal sınırı.
- `anlam_kaymasi`: Günlük ifade, anlamca başka bir hukuki kavrama daha yakın düşüyor (beğenmeyip geri vermek -> ayıplı mal / sözleşmeden dönme, oysa doğru kavram cayma hakkı).
- `benzer_madde_kalabaligi`: Aynı konuyu işleyen çok sayıda madde var (cayma hakkı en az 6 maddede; ön bilgilendirme MSY m.5-8); doğru madde komşularının gerisinde kalıyor.
- `rrf_seyreltmesi`: Yöntemlerden biri doğru maddeyi üst sıralarda bulmuş, diğerinin kötü sıralaması ağırlıksız birleşimde onu ilk 5'in dışına itiyor.

### Hibrit (RRF): 4 başarısız

| Soru | Doğru (sıra) | İlk 3 sonuç | Neden |
|---|---|---|---|
| S06 | MSY:15 (12) | `TKHK:18`, `TKHK:43`, `TKHK:24` | `rrf_seyreltmesi`: Embedding 1. sırada, BM25 21. sırada; birleşimde 12. Başlığı 'Cayma hakkı' olan TKHK m.18/24/43 BM25'te öne geçiyor (benzer madde kalabalığı). |
| S08 | MSY:9/TKHK:48 (16) | `TKHK:45`, `MSY:13`, `TKHK:74` | `anlam_kaymasi`: BM25 2. sırada bulmuş, embedding 24. sırada; birleşimde 16. İlk sıralarda TKHK m.45 (sözleşmeden dönme), MSY m.13, TKHK m.8 (ayıplı mal). |
| S19 | MSY:17 (7) + MSY:16/TKHK:48 (2) | `MSY:12`, `MSY:16`, `MSY:12/A` | `rrf_seyreltmesi`: MSY m.17'yi embedding 2. sırada, BM25 18. sırada buluyor; birleşimde 7. Teslim süresi gereksinimi (MSY m.16) 2. sırada karşılanıyor. |
| S20 | MSY:5 (8) + MSY:7 (2) | `MSY:6`, `MSY:7`, `TKHK:40` | `benzer_madde_kalabaligi`: MSY m.6 (ön bilgilendirme yöntemi), m.7, m.8 aynı konuda; m.5 embedding'de 3., BM25'te 10., birleşimde 8. (RRF seyreltmesi de etkili). |

### Yalnız embedding: 1 başarısız

| Soru | Doğru (sıra) | İlk 3 sonuç | Neden |
|---|---|---|---|
| S08 | MSY:9/TKHK:48 (24) | `TKHK:11`, `TKHK:15`, `TKHK:45` | `anlam_kaymasi`: 'Beğenmedim, geri verebilir miyim' ayıplı mal ve seçimlik haklar maddelerine (TKHK m.11, m.15, m.8) yakın gömülüyor; 'internetten' ifadesi mesafeli sözleşme kavramına bağlanmıyor. |

### Yalnız BM25: 8 başarısız

| Soru | Doğru (sıra) | İlk 3 sonuç | Neden |
|---|---|---|---|
| S06 | MSY:15 (21) | `TKHK:18`, `MSY:11`, `TKHK:24` | `benzer_madde_kalabaligi`: 'cayma' ve 'sözleşme' kelimeleri başlığı 'Cayma hakkı' olan diğer maddelerde de yoğun; MSY m.15'in ayırt edici kelimesi 'istisna' soruda yok. |
| S09 | TKHK:10 (20) | `TKHK:45`, `MSY:22`, `MSY:13` | `kelime_uyusmazligi`: Soru 'bozuldu, kanıtlamalıyım, üç ay' diyor; madde 'ayıp, ispat, altı ay' diyor. |
| S11 | TKHK:7 (15) | `TKHK:79`, `TKHK:76`, `KVKK:11` | `kelime_uyusmazligi`: 'İstemediğim ürünü gönderdiler' ile 'sipariş edilmeyen mal' arasında ortak kök yok. |
| S12 | TKHK:6 (6) | `TKHK:79`, `KVKK:11`, `TKHK:11` | `kelime_uyusmazligi`: 6. sırada, sınırın hemen dışında. 'vitrin' eşleşiyor ama 'satmak' (satma) ile 'satış' (satış) F5 kırpmasında farklı köklere düşüyor. |
| S13 | ETK:8 (15) | `TKHK:77`, `MSY:12/A`, `ETK:Ek 2` | `kelime_uyusmazligi`: 'Kampanya mesajı, durdurmak' ile 'ticari elektronik ileti, reddetme' arasında ortak kelime yok; 'kampanya' TKHK m.77 ve ETK Ek 2'de geçiyor. |
| S14 | KVKK:13 (15) | `TKHK:29`, `TKHK:38`, `KVKK:12` | `kelime_uyusmazligi`: Soru 'bilgilerimi, cevap vermek' diyor; madde 'kişisel veri, başvuru, sonuçlandırır' diyor. |
| S19 | MSY:17 (18) + MSY:16/TKHK:48 (2) | `TKHK:76`, `MSY:16`, `MSY:12` | `kelime_uyusmazligi`: 'Kargo, kaybolan' ile 'taşıyıcı, kayıp, hasar' F5'te eşleşmiyor (kaybo / kayıp). |
| S20 | MSY:5 (10) + MSY:7 (2) | `MSY:6`, `MSY:7`, `MSY:11` | `benzer_madde_kalabaligi`: 'Ön bilgi' kelimeleri MSY m.5-8'in hepsinde ve başlıklarında; içerik maddesi m.5 uzun ve terim yoğunluğu düşük. |

### Neden dağılımı

| Neden | Hibrit (RRF) | Yalnız embedding | Yalnız BM25 |
|---|---|---|---|
| `anlam_kaymasi` | 1 | 1 | 0 |
| `benzer_madde_kalabaligi` | 1 | 0 | 2 |
| `kelime_uyusmazligi` | 0 | 0 | 6 |
| `rrf_seyreltmesi` | 2 | 0 | 0 |

## 6. Genel gözlemler

- Bu sette yalnız embedding her k değerinde hibritten iyi (@5: 20/21'e karşı 17/21). Ağırlıksız RRF, BM25'in kötü olduğu günlük dil sorularında embedding'in doğru sonucunu aşağı çekiyor (S06, S19). Tersine BM25'in kurtardığı tek soru S08 (BM25 2., embedding 24.); orada da hibrit 16. sırada kalıyor.
- Hibritin @1 kaybı (8/21'e karşı embedding 12/21) büyük ölçüde günlük dil sorularından geliyor: S11 ve S12'de TKHK m.11 (seçimlik haklar) ilk sıraya çıkıyor; şikâyet içeren sorular ayıplı mal maddelerine çekiliyor.
- BM25'in güçlü olduğu madde numarası sorguları ('6502 m.48', '47/A') bu sette yok; hibritin bu sorgulardaki katkısı yalnızca birim testlerde (tests/test_search.py) doğrulanıyor, bu raporda ölçülmüyor.
- Cevapsız sorularda hiçbir yöntemin skoru cevaplılardan ayrışmıyor (ör. embedding'de S25 'trafik cezasına itiraz' 0.630, cevaplı soruların medyanı 0.679). Sabit bir skor eşiği 'cevap yok' demek için yeterli görünmüyor; bu karar cevap üretimi katmanında, getirilen metnin soruyu karşılayıp karşılamadığına bakılarak verilmeli.
- Örneklem küçük: cevaplı 21 soru, bir soru yaklaşık 5 puan. Yöntem seçimi gibi bir karar bu sete göre verilirse (dev setine göre ayar), sonucun holdout setinde doğrulanması gerekir.

