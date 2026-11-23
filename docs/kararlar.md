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
