# mevzuat-rag

Türk e-ticaret ve tüketici mevzuatı üzerinde **kaynak göstererek** soru cevaplayan bir araç (RAG).
Bu depo şu an yalnızca belge işleme ve arama katmanını hedefliyor; cevap üretimi sonraki aşamada.

## Kapsam (docs_raw/)

| Dosya | Belge |
|---|---|
| `1.5.6502.pdf` | 6502 sayılı Tüketicinin Korunması Hakkında Kanun (TKHK) |
| `1.5.6563.pdf` | 6563 sayılı Elektronik Ticaretin Düzenlenmesi Hakkında Kanun (ETK) |
| `1.5.6698.pdf` | 6698 sayılı Kişisel Verilerin Korunması Kanunu (KVKK) |
| `7.5.20237.pdf` | Mesafeli Sözleşmeler Yönetmeliği (MSY) |

Kaynak: mevzuat.gov.tr, indirme tarihi 2026-11-23. `docs_raw/` içindeki dosyalar değiştirilmez.

## Tasarım özeti

- **Parçalama:** madde bazlı; uzun maddeler fıkra, gerekirse bent sınırından bölünür. Her parça
  belge, madde no, madde başlığı, fıkra aralığı, dipnotlar ve değişiklik notlarıyla birlikte tutulur.
- **Arama:** `BAAI/bge-m3` (yerel, çok dilli) + BM25, Reciprocal Rank Fusion ile birleştirilir.
- **Depolama:** veritabanı yok; `data/chunks.jsonl` + numpy dizisi.
- Çekirdek mantık `src/mevzuat_rag/` altında, arayüzden bağımsız.

## Kurulum

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m pip install -e .
.venv\Scripts\python -m pytest
```

## Bilinen sınırlar

_(belge işleme adımında doldurulacak)_
