# Kararlar

Ölçüm sonuçlarından önce sabitlenen kurallar. Her kural, ilgili ölçümden önce commit'lenir.

## Cevap modeli seçimi

- **Kural** (öncelik sırasıyla): (a) yanlış olgu sayısı (elle okuma), (b) yanlış reddetme,
  (c) madde doğruluğu ve olgu oranı, (d) maliyet ve süre.
- **Gürültü payı** (2026-11-23, bir sonraki cevap ölçümünden önce eklendi): Sonnet 5.5 ancak 3
  koşunun toplamında yanlış olgu sayısı Haiku 5.5'ten **en az 2 daha az** ise seçilir; aksi hâlde Haiku.
- Karar ertelendi; çalışma varsayılanı Haiku 5.5. Önceki ölçüm (evals/CEVAP_RAPOR.md, Haiku 2 /
  Sonnet 1) bu kurala göre değerlendirilmez; kural sonraki ölçüm için geçerlidir.

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
