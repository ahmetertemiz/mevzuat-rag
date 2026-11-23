# A15 teşhisi: tablo bağlamdayken neden cevap yok?

Soru: "Bakanlıktan yetki almadan kapıdan satış yapan bir şirkete 2026 yılında ne kadar idari para cezası
uygulanır?" Ölçüm: evals/cevap_kosulari (iki model × 3 koşu). Hiçbir şey değiştirilmedi.

## Gözlem

- Altı koşunun hepsinde bağlamda **TKHK-m77-2** (m.77/4–8, beşinci fıkra dahil) ve **TKHK-tablo2026-1**
  var. Beşinci fıkra: "47 nci maddesinin ikinci fıkrasında belirtilen yükümlülüklere aykırı hareket
  edenler hakkında yüz bin Türk Lirası ..."; tabloda beşinci fıkra: 1.987.014 TL; 446.627 TL.
- Altı koşunun hiçbirinde **TKHK-m47-1** (m.47/2: "İş yeri dışında kurulan sözleşmeler, Bakanlık
  tarafından yetkilendirilmiş satıcı veya sağlayıcı tarafından kurulur.") bağlamda yok.
- Ham çıktıların altısı da `durum: bulunamadi`, cümle yok. Sonnet gerekçeyi açıkça yazıyor (koşu 1):
  "yetki almadan kapıdan satış yapılmasına ilişkin yükümlülüğü ve buna bağlı idari para cezasını düzenleyen
  hüküm sağlanan parçalarda yer almamaktadır". Haiku yalnızca sorunun kendisini "bulunamayan"a yazıyor.

## Neden

Cevap bir **atıf zinciri** gerektiriyor: soru (yetkisiz kapıdan satış) → m.47/2 (yetkilendirme
yükümlülüğü) → m.77/5 (cezayı m.47/2'ye numarayla bağlıyor) → 2026 tablosu (beşinci fıkra). Bağlamda
zincirin ikinci halkası yok. m.77/5 yükümlülüğü yalnız madde numarasıyla anıyor; "yetki" ya da
"kapıdan satış" kelimesi geçmiyor. Modelin 47/2'nin yetkilendirme olduğunu bilmesi için ya genel
bilgisini kullanması (kural 1 yasaklıyor) ya da m.47 metnini görmesi gerekir. İki model de kurala uydu.

Yani bu bir üretim hatası değil, **bağlam eksikliği**. Önceki raporda "A15'te tablo bağlamda, sorun
üretimde" demiştim; bu yanlıştı. Değerlendirme bunu iki nedenle göstermedi:

1. `evals/answers.yaml`'da A15'in `dayanak` alanı yalnız `TKHK:Tablo-2026` ve `TKHK:77`. Gerekli olan
   `TKHK:47` beklenen maddeler arasında yok, bu yüzden bağlam ölçütü ✓✓✓ gösterdi.
2. Arama, sorudaki "kapıdan satış / yetki" ifadesini kanunun terimine ("iş yeri dışında kurulan
   sözleşme", "yetkilendirilmiş") çevirmedi. Yeniden yazılan sorguların hepsi ceza ve yeniden değerleme
   üzerine; hiçbiri "iş yeri dışında" demiyor. A07 ve A11'deki kavram çevirme sorunuyla aynı tür.

Aynı örüntü A14'te de var: ETK m.12/1'in ilgili bendi bağlamda olmadığı için modeller tablodaki
bendi sipariş teyidi yükümlülüğüne bağlamıyor (Haiku koşu 1 ve Sonnet koşu 2 bunu açıkça yazıyor).

Düzeltme önerilmedi; seçenekler sorulacak.
