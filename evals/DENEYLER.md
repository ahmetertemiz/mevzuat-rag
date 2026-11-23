# Yöntem karşılaştırma deneyleri (geliştirme seti)

`python scripts/experiments.py` tarafından üretilir. Soru seti `evals/retrieval.yaml`: 30 soru, 26 cevaplı (7 madde dili, 8 günlük dil, 6 i̇ki madde, 5 madde numarası), 4 cevapsız. Holdout seti kullanılmadı.

Bu set seçenekleri karşılaştırmak içindir; seçilen yöntem holdout setinde bir kez doğrulanacak. Küçük örneklem: cevaplı 26 soruda bir soru yaklaşık 4 puan.

**Sorgu yeniden yazımı:** `claude-opus-5-5`, effort `low`, yapılandırılmış JSON çıktı; model soruyu cevaplamadan 2-3 sorgu üretir. Özgün soru ve üretilen sorgular ayrı ayrı aranır, tüm sıralamalar ağırlıksız RRF (k=60) ile birleştirilir. Prompt'taki örnekler geliştirme setinden değil, uydurma (`src/mevzuat_rag/rewrite.py`). Ortalama 1153 girdi / 91 çıktı token'ı (çıktıya düşünme token'ları dahil).

## 1. Ana tablo

@k: doğru madde(ler) maddeye indirgenmiş ilk k sonuçta (cevaplı 26 soru). Türe göre sütunlar @5. Bellek: yayın senaryosunda sorgu sırasındaki tepe RSS (`reports/performans_<model>.json`). Süre: soru başına arama medyanı (embedding + BM25 + RRF, özgün ve ek sorgular dahil) + varsa model çağrısının medyan süresi.

| Yöntem | @1 | @3 | @5 | Madde dili @5 | Günlük dil @5 | İki madde @5 | Madde no @5 | Bellek | Sorgu süresi | Model çağrısı / sorgu | Maliyet / sorgu |
|---|---|---|---|---|---|---|---|---|---|---|---|
| BM25 | 11/26 | 15/26 | 18/26 | 6/7 | 3/8 | 4/6 | 5/5 | ~40 MB | 0 ms | 0 | $0 |
| BM25 + yeniden yazım | 16/26 | 19/26 | 23/26 | 6/7 | 8/8 | 4/6 | 5/5 | ~40 MB | 1 ms + 2024 ms çağrı | 1 | $0.0064 |
| bge-m3 embedding | 13/26 | 20/26 | 23/26 | 7/7 | 7/8 | 6/6 | 3/5 | 1896 MB | 60 ms | 0 | $0 |
| bge-m3 embedding + yeniden yazım | 17/26 | 21/26 | 22/26 | 7/7 | 7/8 | 4/6 | 4/5 | 1896 MB | 205 ms + 2024 ms çağrı | 1 | $0.0064 |
| **bge-m3 hibrit** | 12/26 | 21/26 | 22/26 | 6/7 | 7/8 | 4/6 | 5/5 | 1896 MB | 58 ms | 0 | $0 |
| bge-m3 hibrit + yeniden yazım | 17/26 | 22/26 | 24/26 | 7/7 | 8/8 | 5/6 | 4/5 | 1896 MB | 214 ms + 2024 ms çağrı | 1 | $0.0064 |
| granite-97m embedding | 6/26 | 12/26 | 15/26 | 7/7 | 4/8 | 4/6 | 0/5 | 632 MB | 37 ms | 0 | $0 |
| granite-97m embedding + yeniden yazım | 11/26 | 16/26 | 19/26 | 7/7 | 8/8 | 3/6 | 1/5 | 632 MB | 129 ms + 2024 ms çağrı | 1 | $0.0064 |
| granite-97m hibrit | 8/26 | 14/26 | 19/26 | 6/7 | 6/8 | 5/6 | 2/5 | 632 MB | 38 ms | 0 | $0 |
| granite-97m hibrit + yeniden yazım | 15/26 | 21/26 | 23/26 | 7/7 | 8/8 | 4/6 | 4/5 | 632 MB | 129 ms + 2024 ms çağrı | 1 | $0.0064 |
| granite-97m-fp32 embedding | 5/26 | 12/26 | 16/26 | 7/7 | 5/8 | 4/6 | 0/5 | 823 MB | 12 ms | 0 | $0 |
| granite-97m-fp32 embedding + yeniden yazım | 11/26 | 16/26 | 19/26 | 7/7 | 8/8 | 3/6 | 1/5 | 823 MB | 42 ms + 2024 ms çağrı | 1 | $0.0064 |
| granite-97m-fp32 hibrit | 8/26 | 15/26 | 19/26 | 6/7 | 6/8 | 5/6 | 2/5 | 823 MB | 13 ms | 0 | $0 |
| granite-97m-fp32 hibrit + yeniden yazım | 15/26 | 21/26 | 22/26 | 6/7 | 8/8 | 4/6 | 4/5 | 823 MB | 44 ms + 2024 ms çağrı | 1 | $0.0064 |
| e5-small embedding | 8/26 | 12/26 | 16/26 | 7/7 | 4/8 | 2/6 | 3/5 | 1179 MB | 12 ms | 0 | $0 |
| e5-small embedding + yeniden yazım | 13/26 | 16/26 | 21/26 | 7/7 | 7/8 | 3/6 | 4/5 | 1179 MB | 39 ms + 2024 ms çağrı | 1 | $0.0064 |
| e5-small hibrit | 11/26 | 16/26 | 19/26 | 6/7 | 5/8 | 3/6 | 5/5 | 1179 MB | 12 ms | 0 | $0 |
| e5-small hibrit + yeniden yazım | 15/26 | 18/26 | 23/26 | 7/7 | 8/8 | 3/6 | 5/5 | 1179 MB | 41 ms + 2024 ms çağrı | 1 | $0.0064 |

Kalın satır taban çizgisi (şu anki varsayılan). BM25 belleği: torch yüklenmeden süreç RSS'i.

## 2. Soru türüne göre @1 / @3 / @5

| Yöntem | Madde dili | Günlük dil | İki madde | Madde numarası |
|---|---|---|---|---|
| BM25 | 5 / 6 / 6 (n=7) | 1 / 2 / 3 (n=8) | 0 / 2 / 4 (n=6) | 5 / 5 / 5 (n=5) |
| BM25 + yeniden yazım | 6 / 6 / 6 (n=7) | 5 / 6 / 8 (n=8) | 0 / 2 / 4 (n=6) | 5 / 5 / 5 (n=5) |
| bge-m3 embedding | 7 / 7 / 7 (n=7) | 5 / 7 / 7 (n=8) | 0 / 4 / 6 (n=6) | 1 / 2 / 3 (n=5) |
| bge-m3 embedding + yeniden yazım | 7 / 7 / 7 (n=7) | 7 / 7 / 7 (n=8) | 0 / 3 / 4 (n=6) | 3 / 4 / 4 (n=5) |
| bge-m3 hibrit | 6 / 6 / 6 (n=7) | 2 / 7 / 7 (n=8) | 0 / 4 / 4 (n=6) | 4 / 4 / 5 (n=5) |
| bge-m3 hibrit + yeniden yazım | 7 / 7 / 7 (n=7) | 6 / 7 / 8 (n=8) | 0 / 4 / 5 (n=6) | 4 / 4 / 4 (n=5) |
| granite-97m embedding | 5 / 6 / 7 (n=7) | 1 / 4 / 4 (n=8) | 0 / 2 / 4 (n=6) | 0 / 0 / 0 (n=5) |
| granite-97m embedding + yeniden yazım | 4 / 6 / 7 (n=7) | 6 / 8 / 8 (n=8) | 0 / 1 / 3 (n=6) | 1 / 1 / 1 (n=5) |
| granite-97m hibrit | 6 / 6 / 6 (n=7) | 2 / 5 / 6 (n=8) | 0 / 1 / 5 (n=6) | 0 / 2 / 2 (n=5) |
| granite-97m hibrit + yeniden yazım | 5 / 6 / 7 (n=7) | 7 / 8 / 8 (n=8) | 0 / 3 / 4 (n=6) | 3 / 4 / 4 (n=5) |
| granite-97m-fp32 embedding | 4 / 6 / 7 (n=7) | 1 / 4 / 5 (n=8) | 0 / 2 / 4 (n=6) | 0 / 0 / 0 (n=5) |
| granite-97m-fp32 embedding + yeniden yazım | 4 / 6 / 7 (n=7) | 6 / 8 / 8 (n=8) | 0 / 1 / 3 (n=6) | 1 / 1 / 1 (n=5) |
| granite-97m-fp32 hibrit | 6 / 6 / 6 (n=7) | 2 / 5 / 6 (n=8) | 0 / 2 / 5 (n=6) | 0 / 2 / 2 (n=5) |
| granite-97m-fp32 hibrit + yeniden yazım | 6 / 6 / 6 (n=7) | 7 / 8 / 8 (n=8) | 0 / 3 / 4 (n=6) | 2 / 4 / 4 (n=5) |
| e5-small embedding | 6 / 7 / 7 (n=7) | 2 / 3 / 4 (n=8) | 0 / 1 / 2 (n=6) | 0 / 1 / 3 (n=5) |
| e5-small embedding + yeniden yazım | 6 / 7 / 7 (n=7) | 5 / 5 / 7 (n=8) | 0 / 0 / 3 (n=6) | 2 / 4 / 4 (n=5) |
| e5-small hibrit | 5 / 6 / 6 (n=7) | 2 / 4 / 5 (n=8) | 0 / 1 / 3 (n=6) | 4 / 5 / 5 (n=5) |
| e5-small hibrit + yeniden yazım | 5 / 6 / 7 (n=7) | 5 / 6 / 8 (n=8) | 0 / 1 / 3 (n=6) | 5 / 5 / 5 (n=5) |

## 3. Taban çizgisine (bge-m3 hibrit) göre kazandırılan ve kaybettirilen sorular

Kazanç: tabanda başarısız, bu yöntemde başarılı; kayıp: tersi. Parantez içinde doğru maddenin taban → bu yöntem sırası (iki maddeli sorularda en kötü gereksinim).

| Yöntem | @5 kazanç | @5 kayıp | @1 kazanç | @1 kayıp |
|---|---|---|---|---|
| BM25 | S08 (15→2) | S09 (3→21), S11 (2→15), S12 (2→6), S13 (3→15), S14 (3→15) | S30 (5→1) | S01 (1→2), S10 (1→5) |
| BM25 + yeniden yazım | S08 (15→1), S19 (7→5) | S21 (2→8) | S08 (15→1), S09 (3→1), S12 (2→1), S13 (3→1), S30 (5→1) | S10 (1→2) |
| bge-m3 embedding | S06 (12→1), S19 (7→4), S20 (8→3) | S26 (1→11), S30 (5→12) | S06 (12→1), S09 (3→1), S12 (2→1), S14 (3→1) | S26 (1→11), S27 (1→4), S28 (1→2) |
| bge-m3 embedding + yeniden yazım | S06 (12→1), S19 (7→4), S20 (8→2) | S17 (3→8), S21 (2→10), S26 (1→13) | S06 (12→1), S09 (3→1), S11 (2→1), S12 (2→1), S13 (3→1), S14 (3→1), S30 (5→1) | S26 (1→13), S27 (1→2) |
| bge-m3 hibrit + yeniden yazım | S06 (12→1), S08 (15→5), S19 (7→3), S20 (8→5) | S21 (2→6), S26 (1→6) | S06 (12→1), S09 (3→1), S11 (2→1), S12 (2→1), S13 (3→1), S30 (5→1) | S26 (1→6) |
| granite-97m embedding | S06 (12→1), S19 (7→2), S20 (8→4) | S09 (3→29), S13 (3→13), S15 (1→6), S17 (3→8), S18 (2→9), S26 (1→27), S27 (1→59), S28 (1→7), S29 (1→11), S30 (5→61) | S06 (12→1), S12 (2→1) | S05 (1→3), S07 (1→5), S10 (1→2), S15 (1→6), S26 (1→27), S27 (1→59), S28 (1→7), S29 (1→11) |
| granite-97m embedding + yeniden yazım | S06 (12→3), S08 (15→3), S19 (7→5), S20 (8→5) | S16 (3→7), S18 (2→8), S21 (2→10), S26 (1→27), S27 (1→11), S28 (1→6), S30 (5→18) | S09 (3→1), S11 (2→1), S12 (2→1), S13 (3→1) | S05 (1→2), S07 (1→5), S26 (1→27), S27 (1→11), S28 (1→6) |
| granite-97m hibrit | S19 (7→5) | S09 (3→15), S26 (1→8), S27 (1→17), S30 (5→19) | S12 (2→1) | S15 (1→2), S26 (1→8), S27 (1→17), S28 (1→2), S29 (1→3) |
| granite-97m hibrit + yeniden yazım | S06 (12→5), S08 (15→1), S19 (7→3) | S21 (2→8), S26 (1→9) | S08 (15→1), S09 (3→1), S11 (2→1), S12 (2→1), S13 (3→1) | S07 (1→2), S26 (1→9) |
| granite-97m-fp32 embedding | S06 (12→3), S19 (7→2), S20 (8→4) | S09 (3→28), S13 (3→14), S17 (3→7), S18 (2→7), S26 (1→25), S27 (1→61), S28 (1→7), S29 (1→12), S30 (5→61) | S12 (2→1) | S05 (1→3), S07 (1→4), S10 (1→2), S15 (1→5), S26 (1→25), S27 (1→61), S28 (1→7), S29 (1→12) |
| granite-97m-fp32 embedding + yeniden yazım | S06 (12→4), S08 (15→3), S19 (7→5), S20 (8→5) | S16 (3→6), S18 (2→7), S21 (2→10), S26 (1→28), S27 (1→13), S28 (1→8), S30 (5→16) | S09 (3→1), S11 (2→1), S12 (2→1), S13 (3→1) | S05 (1→2), S07 (1→3), S26 (1→28), S27 (1→13), S28 (1→8) |
| granite-97m-fp32 hibrit | S19 (7→5) | S09 (3→14), S26 (1→8), S27 (1→17), S30 (5→17) | S12 (2→1) | S15 (1→2), S26 (1→8), S27 (1→17), S28 (1→2), S29 (1→3) |
| granite-97m-fp32 hibrit + yeniden yazım | S08 (15→1), S19 (7→3) | S21 (2→8), S26 (1→9) | S08 (15→1), S09 (3→1), S11 (2→1), S12 (2→1), S13 (3→1) | S26 (1→9), S27 (1→2) |
| e5-small embedding | S06 (12→3) | S11 (2→30), S13 (3→19), S14 (3→7), S17 (3→6), S21 (2→6), S27 (1→6), S30 (5→10) | S12 (2→1) | S15 (1→4), S26 (1→5), S27 (1→6), S28 (1→2), S29 (1→5) |
| e5-small embedding + yeniden yazım | S06 (12→1), S08 (15→4), S20 (8→5) | S11 (2→14), S16 (3→7), S21 (2→17), S26 (1→6) | S06 (12→1), S09 (3→1), S12 (2→1), S13 (3→1) | S07 (1→2), S26 (1→6), S27 (1→2) |
| e5-small hibrit | — | S11 (2→13), S13 (3→13), S17 (3→6) | — | S01 (1→2) |
| e5-small hibrit + yeniden yazım | S06 (12→4), S08 (15→3), S19 (7→5) | S16 (3→6), S21 (2→12) | S09 (3→1), S12 (2→1), S13 (3→1), S30 (5→1) | S07 (1→2) |

## 4. Yeniden yazımın etkisi (aynı model ve mod, yazımsız → yazımlı)

| Yöntem | @5 kazanç | @5 kayıp | @1 kazanç | @1 kayıp |
|---|---|---|---|---|
| BM25 | S09 (21→1), S11 (15→5), S12 (6→1), S13 (15→1), S14 (15→4), S19 (18→5) | S21 (2→8) | S01 (2→1), S08 (2→1), S09 (21→1), S12 (6→1), S13 (15→1) | — |
| bge-m3 embedding | S30 (12→1) | S17 (5→8), S21 (3→10) | S11 (2→1), S13 (2→1), S28 (2→1), S30 (12→1) | — |
| bge-m3 hibrit | S06 (12→1), S08 (15→5), S19 (7→3), S20 (8→5) | S21 (2→6), S26 (1→6) | S06 (12→1), S09 (3→1), S11 (2→1), S12 (2→1), S13 (3→1), S30 (5→1) | S26 (1→6) |
| granite-97m embedding | S08 (26→3), S09 (29→1), S13 (13→1), S15 (6→1), S17 (8→3), S29 (11→1) | S16 (5→7), S21 (3→10) | S09 (29→1), S10 (2→1), S11 (3→1), S13 (13→1), S15 (6→1), S29 (11→1) | S06 (1→3) |
| granite-97m hibrit | S06 (11→5), S08 (10→1), S09 (15→1), S27 (17→1), S30 (19→3) | S21 (2→8) | S08 (10→1), S09 (15→1), S11 (2→1), S13 (3→1), S15 (2→1), S27 (17→1), S28 (2→1), S29 (3→1) | S07 (1→2) |
| granite-97m-fp32 embedding | S08 (27→3), S09 (28→1), S13 (14→1), S17 (7→3), S29 (12→1) | S16 (5→6), S21 (3→10) | S09 (28→1), S10 (2→1), S11 (3→1), S13 (14→1), S15 (5→1), S29 (12→1) | — |
| granite-97m-fp32 hibrit | S08 (11→1), S09 (14→1), S27 (17→2), S30 (17→3) | S21 (3→8) | S08 (11→1), S09 (14→1), S11 (2→1), S13 (3→1), S15 (2→1), S28 (2→1), S29 (3→1) | — |
| e5-small embedding | S08 (26→4), S13 (19→1), S14 (7→5), S17 (6→4), S20 (9→5), S27 (6→2), S30 (10→2) | S16 (4→7), S26 (5→6) | S06 (3→1), S09 (2→1), S13 (19→1), S15 (4→1), S28 (2→1), S29 (5→1) | S07 (1→2) |
| e5-small hibrit | S06 (12→4), S08 (20→3), S11 (13→5), S13 (13→1), S17 (6→2), S19 (10→5) | S16 (4→6), S21 (4→12) | S01 (2→1), S09 (5→1), S12 (3→1), S13 (13→1), S30 (2→1) | S07 (1→2) |

## 5. Soru bazında doğru maddenin sırası

Her hücre: gereksinim(ler)in maddeye indirgenmiş listedeki sırası (`–` = ilk 30'da yok).

| Soru | Tür | BM25 | BM25 + yeniden yazım | bge-m3 embedding | bge-m3 embedding + yeniden yazım | bge-m3 hibrit | bge-m3 hibrit + yeniden yazım | granite-97m embedding | granite-97m embedding + yeniden yazım | granite-97m hibrit | granite-97m hibrit + yeniden yazım | granite-97m-fp32 embedding | granite-97m-fp32 embedding + yeniden yazım | granite-97m-fp32 hibrit | granite-97m-fp32 hibrit + yeniden yazım | e5-small embedding | e5-small embedding + yeniden yazım | e5-small hibrit | e5-small hibrit + yeniden yazım |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S01 | Madde dili | 2 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 2 | 1 |
| S02 | Madde dili | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| S03 | Madde dili | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| S04 | Madde dili | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| S05 | Madde dili | 1 | 1 | 1 | 1 | 1 | 1 | 3 | 2 | 1 | 1 | 3 | 2 | 1 | 1 | 1 | 1 | 1 | 1 |
| S06 | Madde dili | 21 | 8 | 1 | 1 | 12 | 1 | 1 | 3 | 11 | 5 | 3 | 4 | 12 | 6 | 3 | 1 | 12 | 4 |
| S07 | Madde dili | 1 | 1 | 1 | 1 | 1 | 1 | 5 | 5 | 1 | 2 | 4 | 3 | 1 | 1 | 1 | 2 | 1 | 2 |
| S08 | Günlük dil | 2 | 1 | 24 | 6 | 15 | 5 | 26 | 3 | 10 | 1 | 27 | 3 | 11 | 1 | 26 | 4 | 20 | 3 |
| S09 | Günlük dil | 21 | 1 | 1 | 1 | 3 | 1 | 29 | 1 | 15 | 1 | 28 | 1 | 14 | 1 | 2 | 1 | 5 | 1 |
| S10 | Günlük dil | 5 | 2 | 1 | 1 | 1 | 1 | 2 | 1 | 1 | 1 | 2 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| S11 | Günlük dil | 15 | 5 | 2 | 1 | 2 | 1 | 3 | 1 | 2 | 1 | 3 | 1 | 2 | 1 | 30 | 14 | 13 | 5 |
| S12 | Günlük dil | 6 | 1 | 1 | 1 | 2 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 3 | 1 |
| S13 | Günlük dil | 15 | 1 | 2 | 1 | 3 | 1 | 13 | 1 | 3 | 1 | 14 | 1 | 3 | 1 | 19 | 1 | 13 | 1 |
| S14 | Günlük dil | 15 | 4 | 1 | 1 | 3 | 3 | 3 | 2 | 5 | 3 | 3 | 2 | 5 | 3 | 7 | 5 | 3 | 5 |
| S15 | Günlük dil | 1 | 1 | 1 | 1 | 1 | 1 | 6 | 1 | 2 | 1 | 5 | 1 | 2 | 1 | 4 | 1 | 1 | 1 |
| S16 | İki madde | 2,5 | 3,1 | 1,2 | 2,1 | 1,3 | 2,1 | 1,5 | 7,3 | 1,4 | 5,1 | 1,5 | 6,2 | 1,4 | 5,1 | 4,2 | 7,3 | 1,4 | 6,2 |
| S17 | İki madde | 1,5 | 1,3 | 5,2 | 8,2 | 1,3 | 3,1 | 1,8 | 3,2 | 1,5 | 2,1 | 1,7 | 3,2 | 1,4 | 2,1 | 1,6 | 4,1 | 1,6 | 2,1 |
| S18 | İki madde | 2,1 | 4,1 | 2,1 | 2,1 | 2,1 | 2,1 | 2,9 | 1,8 | 1,4 | 1,2 | 2,7 | 1,7 | 1,3 | 1,2 | 2,1 | 2,4 | 2,1 | 4,1 |
| S19 | İki madde | 18,2 | 3,5 | 2,4 | 4,3 | 7,2 | 2,3 | 1,2 | 5,2 | 5,1 | 3,2 | 1,2 | 5,2 | 5,1 | 3,2 | 9,8 | 10,1 | 10,3 | 5,2 |
| S20 | İki madde | 10,2 | 7,2 | 3,1 | 2,1 | 8,2 | 5,1 | 4,1 | 4,5 | 7,1 | 6,3 | 4,1 | 4,5 | 7,1 | 6,3 | 9,1 | 5,3 | 10,2 | 6,2 |
| S21 | İki madde | 1,2 | 1,8 | 1,3 | 1,10 | 1,2 | 1,6 | 1,3 | 1,10 | 1,2 | 1,8 | 1,3 | 1,10 | 1,3 | 1,8 | 2,6 | 2,17 | 1,4 | 1,12 |
| S26 | Madde numarası | 1 | 1 | 11 | 13 | 1 | 6 | 27 | 27 | 8 | 9 | 25 | 28 | 8 | 9 | 5 | 6 | 1 | 1 |
| S27 | Madde numarası | 1 | 1 | 4 | 2 | 1 | 1 | – | 11 | 17 | 1 | – | 13 | 17 | 2 | 6 | 2 | 1 | 1 |
| S28 | Madde numarası | 1 | 1 | 2 | 1 | 1 | 1 | 7 | 6 | 2 | 1 | 7 | 8 | 2 | 1 | 2 | 1 | 1 | 1 |
| S29 | Madde numarası | 1 | 1 | 1 | 1 | 1 | 1 | 11 | 1 | 3 | 1 | 12 | 1 | 3 | 1 | 5 | 1 | 1 | 1 |
| S30 | Madde numarası | 1 | 1 | 12 | 1 | 5 | 1 | – | 18 | 19 | 3 | – | 16 | 17 | 3 | 10 | 2 | 2 | 1 |

## 6. Üretilen sorgular

- **S01** Mesafeli sözleşmelerde cayma hakkı süresi kaç gündür?  
  → `mesafeli sözleşmelerde cayma hakkı süresi` · `cayma süresinin başlangıcı malın teslimi` · `cayma hakkı on dört gün içinde gerekçe göstermeksizin`
- **S02** Malın ayıplı olması durumunda tüketicinin seçimlik hakları nelerdir?  
  → `ayıplı mal tüketicinin seçimlik hakları` · `ayıplı malda sözleşmeden dönme bedel indirimi ücretsiz onarım` · `ayıplı malın misli ile değiştirilmesi`
- **S03** Ayıplı maldan sorumluluk hangi zamanaşımı süresine tabidir?  
  → `ayıplı maldan sorumluluk zamanaşımı süresi` · `ayıplı mal teslimden itibaren iki yıllık zamanaşımı` · `ayıbın ağır kusur veya hile ile gizlenmesi zamanaşımı`
- **S04** Ticari elektronik iletilerin gönderilmesi için alıcının önceden onayı gerekir mi?  
  → `ticari elektronik ileti gönderiminde alıcının önceden onayı` · `ticari elektronik ileti onay alınmasının istisnaları` · `ticari elektronik iletiyi reddetme hakkı`
- **S05** Kişisel verileri işlenen ilgili kişinin veri sorumlusuna karşı hakları nelerdir?  
  → `ilgili kişinin hakları veri sorumlusuna başvuru` · `kişisel verilerin işlenip işlenmediğini öğrenme hakkı` · `kişisel verilerin silinmesi düzeltilmesi talebi`
- **S06** Tüketicinin cayma hakkını kullanamayacağı sözleşmeler hangileridir?  
  → `cayma hakkının istisnaları` · `cayma hakkı kullanılamayacak mesafeli sözleşmeler` · `tüketicinin istenmesi doğrultusunda kişiselleştirilen mallar cayma hakkı istisnası`
- **S07** Taksitle satış sözleşmesinden cayma hakkı kaç gün içinde kullanılabilir?  
  → `taksitle satış sözleşmesinde cayma hakkı süresi` · `taksitle satış sözleşmesi cayma bildirimi` · `cayma hakkı süresi on dört gün`
- **S08** İnternetten aldığım ayakkabıyı beğenmedim, geri verebilir miyim?  
  → `mesafeli sözleşmelerde cayma hakkı süresi` · `cayma hakkının kullanılması ve malın iadesi` · `mesafeli satışta cayma hakkı bedel iadesi`
- **S09** Aldığım telefon üç ay sonra bozuldu, satıcı kullanıcı hatası diyor. Bozukluğun baştan olduğunu ben mi kanıtlamalıyım?  
  → `ayıplı mal ispat yükü altı ay karinesi` · `teslimden itibaren altı ay içinde ortaya çıkan ayıp` · `ayıplı mal tüketicinin seçimlik hakları`
- **S10** Siparişim bir aydır gelmedi. Satıcının ürünü göndermesi için bir süre sınırı var mı?  
  → `mesafeli sözleşmede siparişin ifa süresi otuz gün` · `satıcının malı teslim yükümlülüğü ve teslimat süresi` · `teslimatın gecikmesi halinde tüketicinin sözleşmeyi feshetme hakkı`
- **S11** Benim istemediğim bir ürünü kapıma gönderdiler, şimdi parasını istiyorlar. Ödemek zorunda mıyım?  
  → `sipariş edilmeyen mal ve hizmetler tüketicinin ödeme yükümlülüğü` · `talep edilmeyen mal teslimi tüketicinin sessiz kalması kabul sayılmaz` · `ataletsiz satış haksız ticari uygulama`
- **S12** Mağaza vitrinde duran ürünü bana satmak istemiyor. Bunu yapmaya hakları var mı?  
  → `satıştan kaçınma yasağı` · `vitrinde teşhir edilen malın satışından kaçınılması` · `satışa arz edilen malın tüketiciye satılmaması`
- **S13** Bir şirketten sürekli kampanya mesajı geliyor. Bunları nasıl durdurabilirim?  
  → `ticari elektronik ileti onay şartı` · `ticari elektronik iletide ret hakkı kullanılması` · `ticari elektronik iletiye ilişkin şikâyet`
- **S14** Bir şirkete bilgilerimi ne yaptığını sordum. Bana ne kadar sürede cevap vermek zorunda?  
  → `ilgili kişinin veri sorumlusuna başvurusu cevaplandırma süresi` · `veri sorumlusuna başvuru otuz gün içinde sonuçlandırma` · `ilgili kişinin kişisel verilerin işlenip işlenmediğini öğrenme hakkı`
- **S15** Arkadaşım yeni üye getirdikçe para kazanacağımız bir sisteme girmemi istiyor. Bu yasal mı?  
  → `saadet zinciri piramit satış sistemi yasağı` · `doğrudan satış sistemlerinde yeni katılımcı getirme karşılığı gelir` · `piramit satış sistemi oluşturulması yasak`
- **S16** İnternetten aldığım ürün için cayma hakkımı kullandım. Ürünü kaç gün içinde geri göndermeliyim, satıcı da paramı kaç gün içinde iade etmeli?  
  → `cayma hakkı kullanıldığında tüketicinin malı geri gönderme süresi` · `cayma hakkında satıcının bedeli iade yükümlülüğü süresi` · `mesafeli sözleşmede cayma hakkının kullanımında tarafların yükümlülükleri`
- **S17** Garanti süresi içinde onarılan ürün tekrar arızalanırsa hangi haklarımı kullanabilirim?  
  → `garanti süresi içinde arızanın tekrarlanması malın ücretsiz değiştirilmesi` · `ayıplı mal tüketicinin seçimlik hakları sözleşmeden dönme bedel iadesi` · `onarım süresi garanti belgesi azami tamir süresi`
- **S18** Tüketici hakem heyetine hangi tutarın altındaki uyuşmazlıklarda başvurulur, bu tutarın üstünde dava açmadan önce arabulucuya gitmek zorunlu mu?  
  → `tüketici hakem heyetine başvuru parasal sınır` · `tüketici mahkemesinde dava şartı arabuluculuk` · `tüketici uyuşmazlıklarında zorunlu arabuluculuk`
- **S19** Kargoda kaybolan üründen kim sorumludur ve satıcı ürünü en geç kaç gün içinde teslim etmek zorundadır?  
  → `malın teslimine kadar kayıp ve hasardan satıcının sorumluluğu` · `mesafeli sözleşmelerde malın teslim süresi otuz gün` · `taşıyıcıya teslimde hasar ve kayıp riski mesafeli satış`
- **S20** İnternet satışında satıcı sözleşme kurulmadan önce hangi bilgileri vermek zorundadır ve bu ön bilgilerin alındığı nasıl teyit edilir?  
  → `mesafeli sözleşmelerde ön bilgilendirme yükümlülüğü` · `ön bilgilendirme içeriği satıcının kimlik bilgileri ve cayma hakkı` · `ön bilgilerin alındığının teyidi kalıcı veri saklayıcısı`
- **S21** Kişisel verilerimin silinmesini isteyebilir miyim ve bu talebimi veri sorumlusuna hangi yolla iletirim?  
  → `kişisel verilerin silinmesi, yok edilmesi veya anonim hale getirilmesi` · `ilgili kişinin veri sorumlusuna başvuru usulü` · `ilgili kişinin hakları kişisel verilerin silinmesini isteme`
- **S22** Kiracının depozitosunu ev sahibi ne zaman iade etmek zorundadır?  
  → `kira sözleşmesinde güvence bedelinin iadesi` · `kiracının güvence teminatı geri ödenmesi süresi` · `konut kirası depozito iadesi kiraya veren yükümlülüğü`
- **S23** İnternetten yapılan satışlarda KDV oranı yüzde kaç uygulanır?  
  → `mesafeli sözleşmelerde vergiler dahil toplam fiyat` · `elektronik ticarette satış fiyatına katma değer vergisi dahil edilmesi` · `katma değer vergisi oranı mal teslimi`
- **S24** İşten çıkarılan bir çalışanın kıdem tazminatı nasıl hesaplanır?  
  → `kıdem tazminatı hesaplanması` · `iş sözleşmesinin işveren tarafından feshi kıdem tazminatı` · `kıdem tazminatına esas ücret ve hizmet süresi`
- **S25** Trafik cezasına itiraz süresi kaç gündür?  
  → `trafik idari para cezasına itiraz süresi` · `idari yaptırım kararına karşı sulh ceza hakimliğine başvuru süresi`
- **S26** 6502 sayılı kanunun 56. maddesi ne diyor?  
  → `6502 sayılı Kanun madde 56` · `6502 sayılı Tüketicinin Korunması Hakkında Kanun 56. madde`
- **S27** KVKK 5. madde  
  → `KVKK madde 5` · `kişisel verilerin işlenme şartları açık rıza` · `açık rıza aranmaksızın kişisel veri işlenmesi halleri`
- **S28** Elektronik Ticaretin Düzenlenmesi Hakkında Kanun ek 2. madde neyi düzenler?  
  → `Elektronik Ticaretin Düzenlenmesi Hakkında Kanun ek madde 2` · `6563 sayılı Kanun ek madde 2` · `elektronik ticaret pazar yeri hizmet sağlayıcı yükümlülükleri`
- **S29** Mesafeli Sözleşmeler Yönetmeliği'nin 15. maddesi  
  → `Mesafeli Sözleşmeler Yönetmeliği madde 15` · `Mesafeli Sözleşmeler Yönetmeliği cayma hakkının istisnaları` · `mesafeli sözleşmelerde cayma hakkı kullanılamayacak durumlar`
- **S30** Tüketicinin Korunması Hakkında Kanun madde 73/A  
  → `Tüketicinin Korunması Hakkında Kanun madde 73/A` · `6502 sayılı Kanun 73/A tüketici hakem heyeti arabuluculuk dava şartı` · `tüketici uyuşmazlıklarında dava açılmadan önce arabulucuya başvuru`

## 7. Yorum

Bu bölüm sonuçlara bakılarak elle yazıldı. Hiçbir ayar değiştirilmedi; varsayılan hâlâ `bge-m3 hibrit`.

**Yeniden yazım her yapılandırmada @1'i artırıyor.** Artış +4 ile +7 soru arasında. @5'te de bir yapılandırma dışında artış var; istisna yalnız bge-m3 embedding (23 → 22). En büyük kazanç BM25'te: @5 18 → 23, günlük dil 3/8 → 8/8. BM25'in yapısal zayıflığı olan kelime uyuşmazlığını (`kargo` / `taşıyıcı`, `kampanya mesajı` / `ticari elektronik ileti`) model çağrısı kapatıyor. Bedeli soru başına bir model çağrısı: ortalama $0.0064 (`claude-opus-5-5`, effort `low`) ve medyan yaklaşık 2 saniye ek gecikme. Bu, aramanın kendisinden 10 ile 100 kat daha uzun.

**Yeniden yazımın tutarlı iki kaybı var:**
- **S21 (iki konulu soru):** Üretilen üç sorgudan ikisi "silme" konusunu, biri "başvuru" konusunu hedefliyor. RRF çok listede geçen maddeyi öne aldığı için KVKK m.13 geriye düşüyor. Bu kayıp 9 yazımlı yapılandırmanın 8'inde görülüyor.
- **S26 (madde numarası):** Üretilen sorgular madde numarasını koruyor ve BM25 doğru maddeyi buluyor. Ama aynı sorgular embedding'e de giriyor; embedding numarayı anlamsal olarak çözemediği için ürettiği sıralamalar gürültü ekliyor. bge-m3 ve Granite hibritlerinde birleşim doğru maddeyi 1. sıradan 6.–9. sıraya itiyor. Yazımlı BM25'te bu kayıp yok.

**Küçük embedding modelleri bu sette belleklerini hak etmiyor:**
- **Granite-97M:** Yazımsız hâlde bge-m3'ün belirgin gerisinde (@5 hibrit 19'a karşı 22). En zayıf olduğu tür madde numarası soruları (embedding 0/5). Float32 ile bfloat16 arasında kalite farkı yok. Float32 sürümü bu işlemcide yaklaşık 2,5 kat daha hızlı (16 ms'ye karşı 40 ms), sorgu sırasında 823 MB kullanıyor.
- **e5-small:** 512 token sınırı yüzünden 34 parça kesiliyor. Ölçülen bellek 1.179 MB, yani 1 GB hedefinin üstünde.
- **Karşılaştırma:** İki küçük model de yazımla birlikte bile yazımlı BM25'i geçemiyor. Yazımlı BM25 aynı @5'i (23/26) torch yüklemeden, yaklaşık 40 MB ile veriyor.

**Farklar küçük.** Cevaplı 26 soruda bir soru yaklaşık 4 puan. En iyi üç yapılandırma arasındaki fark @5'te 1 soru, @1'de 1–2 soru. Bu fark tek başına bir sıralama kurmaya yetmez; seçilen yöntem holdout setinde doğrulanmalı.

## 8. Öneri (uygulanmadı)

Kararı barındırma ortamının belleği belirliyor. İki aday var:

| | A: `bge-m3 hibrit + yeniden yazım` | B: `BM25 + yeniden yazım` |
|---|---|---|
| @1 / @3 / @5 (26) | 17 / 22 / 24 | 16 / 19 / 23 |
| Bellek (sorgu tepe) | ~1,9 GB (+ torch) | ~40 MB, torch gerekmez |
| Sorgu süresi | ~250 ms + ~2 sn çağrı | ~1 ms + ~2 sn çağrı |
| Maliyet / sorgu | $0.0064 | $0.0064 |
| Model API'si çalışmazsa | bge-m3 hibrit'e düşer (@5 22/26) | düz BM25'e düşer (@5 18/26, günlük dil 3/8) |

**Önerim: B (`BM25 + yeniden yazım`).** Gerekçem, ücretsiz barındırma hedefi. B, bu sette A'dan yalnızca 1 soru geride; bellek ihtiyacı ise yaklaşık 50 kat küçük. Torch ve embedding modeli kurulumunu, yaklaşık 9 saniyelik soğuk başlangıcı ve 4 GB'lık model önbelleğini de ortadan kaldırıyor. B'nin zayıf yanları:
- API'ye tam bağımlı. Çağrı başarısız olursa kalite belirgin biçimde düşer.
- Gecikmenin neredeyse tamamı model çağrısından geliyor.

Holdout öncesinde senin karar vermen gereken noktalar:

1. **Yeniden yazım modeli.** Ölçüm `claude-opus-5-5` ile yapıldı; varsayılan model bu. Daha ucuz bir modele (ör. `claude-haiku-5-5`) geçmek maliyeti ve gecikmeyi düşürebilir, ama bu ölçülmedi. Geçilecekse önce bu geliştirme setinde ölçülmeli.
2. **S21 ve S26 kayıpları için olası düzeltmeler.** Örnekler: madde numarası içeren sorgularda yalnız BM25 kullanmak ya da özgün sorguya daha yüksek ağırlık vermek. Bunlar bu sete göre ayar yapmak olur; yapılacaksa holdout'tan önce yapılmalı ve holdout bir kez koşulmalı.
3. **Holdout'ta neyin koşulacağı.** Yalnızca seçilen yapılandırma mı, yoksa A ve B birlikte mi? İkisini birlikte koşmak holdout üzerinde seçim yapmak anlamına gelir; öneri tek yapılandırma.

