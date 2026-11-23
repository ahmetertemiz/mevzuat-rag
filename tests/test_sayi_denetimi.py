"""Sorgu yeniden yazımında sayı denetimi: soruda geçmeyen sayı içeren sorgu atılır."""
import json
from types import SimpleNamespace

import pytest

from mevzuat_rag import rewrite
from mevzuat_rag.pipeline import BASARISIZ, UYGULANDI, Arayici
from mevzuat_rag.retrieve import Retriever
from mevzuat_rag.rewrite import Rewrite, denetle, sayi_denetimi


@pytest.mark.parametrize("soru,sorgu", [
    ("cayma hakkı kaç gün", "cayma hakkı süresi on dört gün"),   # yazıyla süre
    ("cayma hakkı kaç gün", "cayma süresi 14 gün"),              # rakamla süre
    ("ürünü geri göndermem gerekiyor", "malın iadesi on günde"),  # ekli biçim
    ("zamanaşımı ne kadar", "iki yıllık zamanaşımı"),
    ("ceza ne kadar", "idari para cezası yüzde on"),             # oran
    ("abonelik iptali", "abonelik sözleşmesi bir yıl"),
    ("kişisel verilerimi silebilir miyim", "6698 madde 11 ilgili kişinin hakları"),  # madde no (11)
    ("kargo kayboldu", "1618 sayılı Kanun taşıma"),             # belge kaydında olmayan kanun no
    ("mesafeli satış", "Mesafeli Sözleşmeler Yönetmeliği 20237"),  # yönetmelik kayıt no kanun no değil
    ("ödeme ne zaman yapılır", "beş iş günü içinde ödeme"),
])
def test_soruda_olmayan_sayi_atilir(soru, sorgu):
    assert sayi_denetimi(soru, sorgu) is not None


@pytest.mark.parametrize("soru,sorgu", [
    ("cayma hakkı kaç gün", "mesafeli sözleşmelerde cayma hakkı süresi"),
    ("6502 sayılı kanunun 56. maddesi ne diyor?", "6502 sayılı Kanun madde 56"),  # soruda var
    ("telefon üç ay sonra bozuldu", "üç ay içinde ortaya çıkan ayıp"),           # soruda var
    ("Tüketicinin Korunması Hakkında Kanun madde 73/A", "73/A dava şartı arabuluculuk"),
    ("ayıplı ürün", "bir ayıplı mal için seçimlik haklar"),      # "bir" + "ayıp" süre değil
    ("iade", "bir ürünün iadesi"),
    ("ön bilgi", "ön bilgilendirme yükümlülüğü"),
    # belge kaydındaki kanun numaraları, adlar ve kısaltmalar serbest
    ("kargo kayboldu", "6502 sayılı Kanun mesafeli sözleşme"),
    ("KVKK 5. madde", "6698 sayılı Kanun madde 5"),
    ("e-ticaret bildirimi", "6563 sayılı Elektronik Ticaretin Düzenlenmesi Hakkında Kanun"),
    ("mesafeli satış", "Mesafeli Sözleşmeler Yönetmeliği MSY cayma"),
])
def test_soruda_olan_ya_da_sayi_olmayan_sorgu_kalir(soru, sorgu):
    assert sayi_denetimi(soru, sorgu) is None


def test_denetle_sirayi_korur_ve_nedeni_kaydeder():
    kalan, atilan = denetle("cayma hakkı kaç gün", ["cayma hakkı süresi", "on dört gün cayma", "cayma bildirimi"])
    assert kalan == ["cayma hakkı süresi", "cayma bildirimi"]
    assert atilan == [{"sorgu": "on dört gün cayma", "neden": "soruda olmayan süre/tutar/oran: on dört gün"}]


def test_promptta_kural_var():
    assert rewrite.PROMPT_VERSION >= 3
    assert "Soruda geçmeyen hiçbir sayı ekleme" in rewrite.SYSTEM_PROMPT
    assert "Cevabı tahmin" in rewrite.SYSTEM_PROMPT


def test_rewrite_cagrisi_denetimi_uygular(monkeypatch):
    """QueryRewriter.rewrite, model çıktısını denetimden geçirir (API çağrısı taklit edilir)."""
    fake_resp = SimpleNamespace(
        stop_reason="end_turn",
        content=[SimpleNamespace(type="text", text=json.dumps(
            {"sorgular": ["cayma hakkı süresi", "cayma süresi 14 gün"]}))],
        usage=SimpleNamespace(input_tokens=100, output_tokens=10),
    )
    rw = rewrite.QueryRewriter.__new__(rewrite.QueryRewriter)
    rw.model, rw.effort = "claude-haiku-5-5", "low"
    rw.client = SimpleNamespace(messages=SimpleNamespace(create=lambda **kw: fake_resp))
    r = rw.rewrite("cayma hakkı kaç gün")
    assert r.sorgular == ["cayma hakkı süresi"]
    assert r.atilan_sorgular[0]["sorgu"] == "cayma süresi 14 gün"


@pytest.fixture(scope="module")
def bm25():
    return Retriever(load_model=False)


class FakeRW:
    def __init__(self, kalan, atilan):
        self.kalan, self.atilan = kalan, atilan

    def rewrite(self, q):
        return Rewrite(q, self.kalan, "sahte", 1, 1, 0.0, 0.1, "end_turn", self.atilan)


def test_sonuc_nesnesi_atilan_sorgulari_belirtir(bm25):
    at = [{"sorgu": "cayma süresi 14 gün", "neden": "soruda olmayan sayı: 14"}]
    s = Arayici(retriever=bm25, rewriter=FakeRW(["cayma hakkı süresi"], at)).ara("cayma hakkı kaç gün")
    assert s.yeniden_yazim == UYGULANDI and s.atilan_sorgular == at and s.uyari is None


def test_hepsi_atilirsa_duz_bm25_ve_uyari(bm25):
    at = [{"sorgu": "14 gün", "neden": "soruda olmayan sayı: 14"}]
    s = Arayici(retriever=bm25, rewriter=FakeRW([], at)).ara("cayma hakkı kaç gün", k=3)
    assert s.yeniden_yazim == BASARISIZ and "sayı denetiminde atıldı" in s.uyari
    assert [h.chunk["chunk_id"] for h in s.hits] == \
        [h.chunk["chunk_id"] for h in bm25.search("cayma hakkı kaç gün", k=3, mode="bm25")]
