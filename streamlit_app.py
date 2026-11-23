"""Mevzuat RAG arayüzü: `streamlit run streamlit_app.py`.

Anahtar: önce st.secrets["ANTHROPIC_API_KEY"], yoksa ortam / .env. Ziyaretçi kendi anahtarını yan
panelden girebilir; o anahtar yalnızca o oturumun istemcisine verilir, ekrana, günlüğe ya da süreç
ortamına yazılmaz. Ortak anahtarla yapılan her model çağrısı günlük sınırdan düşer (bellekte tutulur).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from mevzuat_rag.answer import CEVAP_MODEL, KAPANIS  # noqa: E402
from mevzuat_rag.arayuz import (VARSAYILAN_GUNLUK_SINIR, GunlukSayac, SayacliIstemci,  # noqa: E402
                                SinirAsildi, cevap_yukle, cevaplayici_kur, kisa_atif, madde_tam_metni,
                                ornek_cevaplari_oku)
from mevzuat_rag.context import belge_kaydi  # noqa: E402
from mevzuat_rag.retrieve import Retriever  # noqa: E402
from mevzuat_rag.rewrite import REWRITE_MODEL, load_dotenv  # noqa: E402

SORU_AZAMI = 500
ORNEK_SORULAR = [
    "Abonelik sözleşmesini nasıl sona erdirebilirim, bunun için ücret ödemem gerekir mi?",
    "Satın aldığım ürün için garanti belgesi verilmesi zorunlu mu, garanti süresi en az ne kadardır?",
    "Kişisel verilerim yurt dışına aktarılabilir mi?",
    "Üretici, sattığı ürün için satış sonrası servis hizmetini ne kadar süre sağlamak zorundadır?",
    "Ön ödemeli konut satışında tüketici sözleşmeden ne zaman cayabilir?",
]
UYARI_BASLIK = {
    "aym_iptal": ("Anayasa Mahkemesi iptal kararı", ":material/gavel:"),
    "mulga": ("Yürürlükten kaldırılmış hüküm", ":material/block:"),
    "sistem_hatasi": ("Sistem hatası", ":material/error:"),
    "tutar_guncellenir": ("Tutar güncellenir", ":material/currency_lira:"),
    "ceza_tutari_belirsiz": ("Ceza tutarı belirsiz", ":material/help:"),
    "gecis_hukmu": ("Geçiş / yürürlük hükmü", ":material/schedule:"),
    "diger": ("Uyarı", ":material/info:"),
}
BELIRGIN = ("aym_iptal", "mulga", "sistem_hatasi")

st.set_page_config(page_title="Mevzuat RAG", page_icon=":material/balance:", layout="centered")


# ------------------------------------------------------------------ paylaşılan kaynaklar

def _ayar(ad: str) -> str | None:
    try:
        if ad in st.secrets:
            return str(st.secrets[ad])
    except Exception:  # secrets.toml yok
        pass
    load_dotenv()
    return os.environ.get(ad) or None


@st.cache_resource
def retriever() -> Retriever:
    return Retriever(load_model=False)


@st.cache_resource
def belgeler() -> dict[str, dict]:
    return belge_kaydi()


@st.cache_resource
def ornek_kayit() -> dict:
    return ornek_cevaplari_oku()


@st.cache_resource
def sayac() -> GunlukSayac:
    try:
        sinir = int(_ayar("GUNLUK_CAGRI_SINIRI") or VARSAYILAN_GUNLUK_SINIR)
    except ValueError:
        sinir = VARSAYILAN_GUNLUK_SINIR
    return GunlukSayac(sinir)


@st.cache_resource
def ortak_ham_istemci():
    anahtar = _ayar("ANTHROPIC_API_KEY")
    if not anahtar:
        return None
    import anthropic
    return anthropic.Anthropic(api_key=anahtar, timeout=60.0, max_retries=2)


def esc(metin: str) -> str:
    """Markdown özel karakterlerini kaçır; satır sonlarını koru."""
    out = metin or ""
    for ch in "\\`*_[]#<>|~$":
        out = out.replace(ch, "\\" + ch)
    return out.replace("\n", "  \n")


# ------------------------------------------------------------------ durum

st.session_state.setdefault("soru", "")
st.session_state.setdefault("calistir", False)
st.session_state.setdefault("sonuc", None)


def ornek_sec(q: str) -> None:
    st.session_state.soru = q
    st.session_state.calistir = True


# ------------------------------------------------------------------ yan panel: anahtar

with st.sidebar:
    st.header("Anahtar ve sınır", divider="gray")
    ziyaretci_anahtari = st.text_input(
        "Kendi Anthropic API anahtarınız (isteğe bağlı)", type="password", key="ziyaretci_anahtari",
        help="Girerseniz çağrılar sizin anahtarınızla yapılır ve ortak günlük sınırdan düşmez. "
             "Anahtar yalnızca bu oturumda sunucu belleğinde tutulur; kaydedilmez, ekrana ya da günlüğe "
             "yazılmaz.")
    ortak = ortak_ham_istemci()
    kota_yeri = st.container()   # sayfa sonunda doldurulur: kalan sayı bu çalıştırmadaki çağrıları da içersin
    st.caption(f"Modeller: yeniden yazım `{REWRITE_MODEL}`, cevap `{CEVAP_MODEL}`")


# ------------------------------------------------------------------ ana sayfa

st.title("Mevzuat RAG", anchor=False)
st.caption("Tüketici, e-ticaret, mesafeli sözleşmeler ve kişisel verilerin korunması mevzuatı hakkında "
           "kaynaklı cevaplar. Her cümle kelimesi kelimesine bir alıntıyla doğrulanır.")

st.text_area("Sorunuz", key="soru", max_chars=SORU_AZAMI, height=90,
             placeholder="Ör. Mesafeli satışta satıcı ürünü en geç ne zaman teslim etmeli?")
with st.container(horizontal=True, vertical_alignment="center"):
    sor = st.button("Sor", key="sor", type="primary", icon=":material/search:",
                    disabled=not (ziyaretci_anahtari or ortak is not None))
    st.caption("ya da bir örnek seçin:")
with st.container(horizontal=True, gap="small"):
    for i, q in enumerate(ORNEK_SORULAR):
        st.button(q, key=f"ornek_{i}", on_click=ornek_sec, args=(q,), type="tertiary")


def kayitli_cevap(soru: str) -> dict | None:
    """Örnek sorunun kayıtlı cevabı (data/ornek_cevaplar.json); canlı cevapla aynı biçimde döner."""
    k = ornek_kayit()
    v = (k.get("cevaplar") or {}).get(soru)
    if v is None:
        return None
    return {"cevap": cevap_yukle(v["cevap"]), "cagri": v.get("cagri"),
            "kayitli": {"tarih": k.get("uretim_tarihi"), "model": k.get("model")}}


def cevapla(soru: str) -> dict:
    if not ziyaretci_anahtari and ortak is None:
        return kayitli_cevap(soru) or {"hata": "anahtarsiz"}
    if ziyaretci_anahtari:
        import anthropic
        istemci = SayacliIstemci(anthropic.Anthropic(api_key=ziyaretci_anahtari, timeout=60.0, max_retries=2), None)
    else:
        s = sayac()
        if s.kalan() < 2:
            return {"hata": "sinir"}
        istemci = SayacliIstemci(ortak, s)
    try:
        import anthropic
        cevap = cevaplayici_kur(retriever(), istemci).cevapla(soru)
    except SinirAsildi:
        return {"hata": "sinir"}
    except anthropic.AuthenticationError:
        return {"hata": "anahtar"}
    except anthropic.APIError:
        return {"hata": "api"}
    return {"cevap": cevap, "cagri": istemci.cagri_sayisi}


calistir = sor or st.session_state.calistir
st.session_state.calistir = False
soru = (st.session_state.soru or "").strip()
if calistir and soru:
    with st.spinner("Belgelerde aranıyor ve cevap doğrulanıyor..."):
        st.session_state.sonuc = cevapla(soru)
elif calistir:
    st.warning("Önce bir soru yazın.")

HATA_MESAJI = {
    "sinir": ("Günlük sınır doldu", "Ortak anahtarın bugünkü çağrı sınırı doldu. Yarın yeniden deneyin "
              "ya da yan panelden kendi API anahtarınızı girin."),
    "anahtar": ("Anahtar geçersiz", "Anthropic API anahtarı kabul edilmedi. Yan paneldeki anahtarı kontrol edin."),
    "api": ("Servise ulaşılamadı", "Model servisine şu anda ulaşılamıyor. Biraz sonra yeniden deneyin."),
    "anahtarsiz": ("API anahtarı gerekli", "Kendi sorunuzu sormak için yan panelden Anthropic API anahtarınızı "
                   "girin. Örnek sorular anahtarsız görüntülenebilir."),
}

sonuc = st.session_state.sonuc
cevap = (sonuc or {}).get("cevap")
if sonuc and sonuc.get("hata"):
    baslik, govde = HATA_MESAJI[sonuc["hata"]]
    if sonuc["hata"] == "anahtarsiz":   # hata değil, yönlendirme: sakin bilgi notu
        st.info(govde, title=baslik, icon=":material/key:")
    else:
        st.error(govde, title=baslik, icon=":material/error:")
elif cevap is not None:
    tum = retriever().chunks
    by_id = {c["chunk_id"]: c for c in tum}
    B = belgeler()
    st.subheader("Cevap", anchor=False, divider="gray")
    if sonuc.get("kayitli"):
        st.info(f"Kayıtlı örnek cevap (üretim tarihi {sonuc['kayitli'].get('tarih')}, model "
                f"`{sonuc['kayitli'].get('model')}`); kendi sorunuzu sormak için yan panelden API "
                "anahtarınızı girin.", icon=":material/history:")
    st.caption(f"Soru: {esc(cevap.soru)}")

    # --- üstte: belirgin uyarılar, sonra diğer uyarılar, sonra çıkarılan cümle notu
    sirali = sorted(cevap.uyarilar, key=lambda u: 0 if u["tur"] in BELIRGIN else 1)
    sistem_hatasi = any(u["tur"] == "sistem_hatasi" for u in cevap.uyarilar)
    for u in sirali:
        baslik, ikon = UYARI_BASLIK.get(u["tur"], UYARI_BASLIK["diger"])
        kaynak = "" if u.get("kaynak") == "kod" else "  \n*Model uyarısı; dayanağı kaynakta doğrulandı.*"
        (st.error if u["tur"] in BELIRGIN else st.warning)(esc(u["metin"]) + kaynak, title=baslik, icon=ikon)
    if cevap.ust_not:
        st.info(esc(cevap.ust_not) + " Çıkarılan cümleler gösterilmez.", icon=":material/content_cut:")

    # --- durum
    if sistem_hatasi:
        pass   # sistem hatası "belgelerde yok" anlamına gelmez; yukarıda gösterildi
    elif cevap.durum == "bulunamadi":
        eksik = "".join(f"\n- {esc(b)}" for b in cevap.bulunamayan)
        st.info(("Verilen belgelerde bu sorunun cevabı bulunamadı." + (f"\n\nBulunamayan:{eksik}" if eksik else "")),
                title="Belgelerde bulunamadı", icon=":material/search_off:")
    elif cevap.durum == "kismen_cevaplandi":
        eksik = "".join(f"\n- {esc(b)}" for b in cevap.bulunamayan)
        govde = ("Sorunun bir kısmı belgelerde var; aşağıdaki kısım bulunamadı:" + eksik if eksik else
                 "Bazı cümleler kaynağında doğrulanamadığı için çıkarıldı; aşağıdaki cevap eksik olabilir.")
        st.warning(govde, title="Kısmen cevaplandı", icon=":material/rule:")

    # --- cümleler ve kaynakları
    for i, c in enumerate(cevap.cumleler):
        with st.container(border=True):
            st.markdown(esc(c.metin))
            with st.container(horizontal=True, gap="small"):
                for j, d in enumerate(c.dayanaklar):
                    p = by_id.get(d["parca_id"])
                    if p is None:
                        continue
                    with st.popover(kisa_atif(p, B, d["alinti"]), icon=":material/format_quote:",
                                    type="tertiary", key=f"pop_{i}_{j}"):
                        st.caption("Kelimesi kelimesine alıntı")
                        st.markdown("> " + esc(d["alinti"]))
                        st.caption(f"{esc(p['belge_adi'])} · {esc(p.get('madde_etiketi') or '')}"
                                   + (f" · {esc(p.get('madde_basligi') or '')}" if p.get("madde_basligi") else ""))
                        st.caption("Maddenin tam metni")
                        with st.container(height=320):
                            st.markdown(esc(madde_tam_metni(p, tum)))

    if cevap.kaynaklar:
        with st.expander("Kaynaklar", icon=":material/menu_book:"):
            for k in cevap.kaynaklar:
                st.markdown(f"- {esc(k['atif'])}")

    # --- yan panel: arama ayrıntıları
    with st.sidebar:
        st.header("Arama ayrıntıları", divider="gray")
        a = cevap.arama
        st.caption(f"Yeniden yazım: **{a.get('yeniden_yazim')}** · model çağrısı: {sonuc.get('cagri')} · "
                   f"maliyet ≈ ${cevap.maliyet_usd:.4f} · süre {cevap.sure_sn:.1f} sn")
        if a.get("uyari"):
            st.caption(f":material/warning: {esc(a['uyari'])}")
        st.markdown("**Yeniden yazılan sorgular**")
        st.markdown("\n".join(f"{n}. {esc(q)}" for n, q in enumerate(a.get("sorgular") or [], 1)) or "—")
        st.markdown("**Bağlama giren parçalar** (sırayla)")
        satirlar = []
        for n, cid in enumerate(cevap.baglam_parcalari, 1):
            p = by_id.get(cid, {})
            satirlar.append({"#": n, "kaynak": kisa_atif(p, B) if p else cid, "parça": cid,
                             "cevapta": "✓" if any(k["parca_id"] == cid for k in cevap.kaynaklar) else ""})
        st.dataframe(satirlar, hide_index=True, alt="Bağlama giren parçalar ve cevapta kullanılanlar")
        st.caption("İlk 8 parça aramadan gelir; sonrakiler ceza tablosu bağlantısıyla eklenir.")

# ------------------------------------------------------------------ alt bilgi

st.divider()
B = belgeler()
st.caption("**Kapsanan belgeler** (kaynak: mevzuat.gov.tr, indirme tarihi: "
           f"{next(iter(B.values())).get('indirme_tarihi')})")
st.caption("\n".join(f"- {esc(b.get('tam_ad') or b.get('belge_adi'))} ({b.get('kisa_ad')})" for b in B.values()))
st.caption(f":material/gavel: **Hukuki tavsiye değildir.** {esc(KAPANIS)} Belgelerin indirme tarihinden "
           "sonraki değişiklikler kapsanmaz.")


with kota_yeri:
    if ziyaretci_anahtari:
        st.caption(":material/key: Sizin anahtarınız kullanılıyor.")
    elif ortak is not None:
        s = sayac()
        st.caption(f":material/speed: Bugün kalan ortak çağrı: **{s.kalan()} / {s.sinir}** "
                   "(soru başına 2 çağrı; UTC gününe göre sıfırlanır)")
    else:
        st.caption(":material/key_off: Ortak anahtar tanımlı değil; soru sormak için kendi anahtarınızı girin.")
