# Kararlar

Ölçüm sonuçlarından önce sabitlenen kurallar. Her kural, ilgili ölçümden önce commit'lenir.

## Cevap modeli seçimi

- **Kural** (öncelik sırasıyla): (a) yanlış olgu sayısı (elle okuma), (b) yanlış reddetme,
  (c) madde doğruluğu ve olgu oranı, (d) maliyet ve süre.
- **Gürültü payı** (2026-11-23, bir sonraki cevap ölçümünden önce eklendi): Sonnet 5.5 ancak 3
  koşunun toplamında yanlış olgu sayısı Haiku 5.5'ten **en az 2 daha az** ise seçilir; aksi hâlde Haiku.
- Önceki ölçüm (evals/CEVAP_RAPOR_v1.md, Haiku 2 / Sonnet 1) bu kurala göre değerlendirilmez;
  kural sonraki ölçüm için geçerlidir.
- **Sonuç (2026-11-23, arama-donduruldu-2 + üç kod düzeltmesi, 3'er koşu, elle okuma):** yanlış olgu
  toplamı Haiku 0, Sonnet 0; fark 0 < 2. **Cevap modeli: Haiku 5.5** (`CEVAP_MODEL` değişmedi).
  Sonnet (b) ve (c)'de biraz iyi (yanlış ret medyanı 2'ye 3, madde doğruluğu 11'e 10), cevap başına
  ~18 kat pahalı. Ayrıntı: evals/CEVAP_RAPOR.md.

## Değerlendirme setleri

- `evals/retrieval.yaml`: geliştirme seti 1 (arama).
- `evals/answers.yaml`: geliştirme seti 2 (cevap üretimi; aramada `dayanak` alanı kullanılır).
  İlk cevap ölçümünde fiilen holdout gibi kullanıldı ve arama orada zayıf çıktı; bu yüzden
  2026-11-23'te geliştirme setine dönüştürüldü ve arama dondurması kaldırıldı.
- `evals/holdout.yaml`: son doğrulama. Soruları proje sahibi yazar; geliştirme sırasında
  koşulmaz, ayar bu sete göre yapılmaz.

## Arama değişikliği kabul kuralı (2026-11-23, ölçümden önce)

Bir arama değişikliği ancak şu iki koşulu **birlikte** sağlarsa kabul edilir:

- **(a)** İki setin toplamında (dev1 26 + dev2 15 = 41 cevaplı soru, k=8 parça) mevcut varsayılana
  göre **en az 3 soru kazanç**.
- **(b)** Hiçbir sette **1 sorudan fazla kayıp** yok.

Uygulama ayrıntıları (ölçümden önce sabitlendi):

- **Ölçüt düzeyi:** Kural **bağlam düzeyinde** uygulanır. Bağlam, `context.kur` ile kurulan ve modele
  giden içerik; ceza tablosu ve bağlı madde eklemeleri dahil. Arama düzeyi (@8) bilgi için raporlanır.
- **Sayım:** Her yapılandırma 3 koşu yapılır. Set başına sonuç, 3 koşunun medyanıdır. Toplam, iki setin
  medyanlarının toplamıdır. Kazanç ve kayıp bu medyanlar üzerinden hesaplanır.
- **Eşleştirme:** Aynı koşuda yeniden yazım soru başına bir kez yapılır. Aynı prompt'u kullanan bütün
  yapılandırmalar (varsayılan dahil) aynı sorguları paylaşır.
- **Birden çok yapılandırma koşulu sağlarsa en basiti seçilir.** Basitlik sırası:
  1. tek değişiklik: 2 (parça çeşitliliği) → 1 (iki aşamalı RRF) → 3 (özgün ifade kuralı)
  2. iki değişiklik: 4 (1+2)
  3. üç değişiklik: 5 (1+2+3)
- **Hiçbiri koşulu sağlamazsa** varsayılan değişmez.
- bge-m3 hibrit (1+2) yalnız referanstır; bellek kısıtı nedeniyle seçilmez.
- Bu turdan sonra arama yeniden dondurulur (git etiketi `arama-donduruldu-2`) ve holdout'a kadar
  değişmez.

### Sonuç (2026-11-23)

Kural uygulandı (`evals/ARAMA_DENEYI.md`). Hiçbir yapılandırma kabul edilmedi; en iyi toplam kazanç +1.
Varsayılan değişmedi: BM25 + yeniden yazım (Haiku 5.5, prompt v3), düz RRF, parça çeşitliliği yok.
Arama `arama-donduruldu-2` etiketiyle yeniden donduruldu; holdout'a kadar değişmez.

## Atıf takibi kabul kuralı (2026-11-23, ölçümden önce)

Değişiklik (bağlam katmanı, `context.py`; arama modülleri değişmez): bağlamdaki bir parça aynı
belgenin başka bir maddesine numarayla atıf yapıyorsa ("47 nci maddesinin ikinci fıkrası"), atıf
yapılan maddenin ilgili parçası bağlama eklenir. Sınırlar:

- Yalnız aramanın **ilk 3 parçasındaki** atıflar (ek parçaların atıfları değil).
- En fazla **3 ek parça**; **tek adım** (eklenen parçanın atıfları izlenmez).
- Yalnız **aynı belge** ("Bu Kanunun", "bu Yönetmeliğin" ya da belge adı olmadan madde numarası).
  "... sayılı Kanunun", başka kanun adı ya da "Kanunu/Kanununun" ile başlayan atıflar dış atıf
  sayılır ve izlenmez. Parçanın kendi maddesine atıf izlenmez.
- **İlgili parça:** atıfta fıkra belirtilmişse (sıra sayısı sözcükle) o fıkrayı içeren parça; yoksa
  maddenin ilk parçası. Bağlamda zaten olan parça eklenmez.
- **Sıralama** (aday 3'ten fazlaysa): adayın soruya BM25 skoru (tablo eklemesindeki gibi), eşitlikte
  atıf sırası.
- Eklenen parça modele "(Aramada çıkmadı; bağlamdaki X parçası numarayla bu maddeye atıf yaptığı için
  eklendi.)" notuyla verilir.

**Kural:** İkisi birlikte sağlanırsa kabul, değilse geri alınır:

- **(a)** İki geliştirme setinin toplamında (dev1 26 + dev2 15) **bağlam düzeyinde en az 2 soru kazanç**.
  Sayım arama değişikliği kuralındaki gibi: her set 3 koşu, set başına medyan, toplam = iki medyanın
  toplamı. Eşleştirilmiş: her koşuda yeniden yazım soru başına bir kez yapılır; atıf takipli ve
  takipsiz bağlam aynı arama sonucundan kurulur.
- **(b)** Cevap değerlendirmesinde (dev2, Haiku 5.5, 3 koşu) **yanlış olgu sayısında artış yok**.
  Karşılaştırma eşleştirilmiş: her koşuda aynı aramayla Haiku hem takipsiz (mevcut sistem: üç kod
  düzeltmesi ve liste bütünlüğü kuralı dahil) hem takipli bağlamla cevaplar; iki kolun 3 koşu
  toplamı elle okumayla karşılaştırılır (ölçütler `evals/cevap_elle_okuma.yaml` ile aynı).
  Takipli kolun toplamı takipsizden büyükse (b) sağlanmaz.

Kabul edilirse atıf takibi varsayılan olur; sistem yeni bir etiketle dondurulur ve holdout bir kez
koşulur.
