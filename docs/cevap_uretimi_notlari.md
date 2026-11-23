# Cevap üretimi notları

Bu dosya, ileride yazılacak cevap üretimi adımının uyması gereken kuralları toplar.
Arama katmanında alınan kararlar burada cevap üretimine taşınır.

## 1. Ceza tutarı soruları

- Tablo parçaları (`tur: "tablo"`, ör. `TKHK-tablo2026-1`, `ETK-tablo2026-1`) **tek başına
  kullanılmaz**.
- Arama sonucunda bir tablo parçası varsa, ilgili satırların `ilgili_parca` alanındaki madde
  parçaları (6502 için 77. madde, 6563 için 12. madde) da bağlama eklenir. Bu parçalar arama
  sonuçlarında çıkmamış olsa bile eklenir.
- Bir satırda birden çok tutar varsa ve tutarın hangi duruma ait olduğu madde metninden
  çıkarılamıyorsa model tahmin yürütmez. Tutarları tablodaki sırayla listeler ve şunu söyler:
  "hangisinin geçerli olduğu 77. maddeye göre belirlenir" (6563 için 12. madde).
- Tutarlar yıla bağlıdır (`yil` alanı, şu an 2026). Cevap bu yılı belirtir.
- Geçici Madde 3 bölümündeki satırlar 77. maddenin değişiklik öncesi hâline aittir. Bu satırlar
  yalnızca geçiş dönemi işlemleri için anlamlıdır ve cevapta bu açıkça belirtilir.

## 2. Dipnotlar

- Her parçanın `dipnotlar` alanı modele verilir: `no`, `tur`, `konum`, `metin`.
- Başlık dipnotları bir maddenin her parçasına kopyalanmıştır. Bağlam kurulurken
  `(belge_id, no)` çiftiyle tekilleştirilir.
- `tur: "aym_karari"` olan dipnotlar (ör. 6563 m.9/1 için tüketici sözleşmeleri yönünden iptal,
  yürürlük 2/3/2027) cevapta mutlaka belirtilir. Yürürlük tarihi de yazılır.

## 3. Mülga maddeler

- `tur: "mulga"` parçası getirilirse cevap, maddenin yürürlükten kaldırıldığını tarih ve
  dayanağıyla birlikte söyler. Madde içeriği hakkında yorum yapmaz.

## 4. Kaynak gösterme

- Her iddia en az bir parçaya dayanır. Kaynak, parçanın `belge_adi`, `madde_etiketi` ve fıkra
  bilgisiyle gösterilir (ör. "6502 sayılı TKHK m.48/4").
