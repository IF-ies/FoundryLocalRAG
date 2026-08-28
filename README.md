# FoundryLocalRAG

Microsoft **Foundry Local** üzerinde çalışan, **tamamen offline** belge soru-cevap asistanı.
Belgelerinizi okur, sorularınızı yalnızca o belgelere dayanarak cevaplar, bilmediğinde
"bilmiyorum" der. Hiçbir veri makineden çıkmaz.

> Bu depo, kurumsal sürüm olan **IF-ies_PrivateAI**'ın temel (PoC) katmanıdır.

---

## Nasıl çalışır

```
Soru
 │
 ├─ 1. Retrieve : soru vektöre çevrilir, SQLite'taki chunk vektörleriyle
 │                kosinüs benzerliği hesaplanır, en yakın K parça seçilir
 │
 ├─ 2. Augment  : seçilen parçalar "BAĞLAM" olarak prompt'a eklenir
 │
 └─ 3. Generate : yerel LLM yalnızca bu bağlamı kullanarak cevap üretir
```

Eşiği (`MIN_SIMILARITY`) geçen hiçbir parça yoksa **model hiç çağrılmaz** ve doğrudan
"bilmiyorum" döner — uydurmaya malzeme verilmez.

## Kullanılan modeller

| Rol | Model | Boyut |
|---|---|---|
| Sohbet | `ministral-3-3b-instruct-2512` | 3.6 GB |
| Embedding | `qwen3-embedding-0.6b` | 478 MB |

Sohbet modeli tahminle değil **ölçülerek** seçildi: altı aday aynı Türkçe sorularla
denendi (`python tools/model_kiyas.py <alias> ...`). Elenenler ve sebepleri
`src/foundry_rag/config.py` içinde yazılıdır.

Foundry Local donanıma uygun varyantı kendisi seçer (CUDA GPU varsa onu kullanır).
Model değiştirmek için kod düzenlemeye gerek yok:

```bash
set FOUNDRY_RAG_CHAT_MODEL=qwen2.5-7b
```

## Kurulum

**Gereken:** Windows 10/11, Python 3.11+ (3.13 ile test edildi), ~5 GB disk.

```bash
# 1. Foundry Local
winget install Microsoft.FoundryLocal
foundry --version

# 2. Python ortamı
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

İlk çalıştırmada modeller indirilir (**internet gerekir**). Sonrasında her şey offline.

### Model cache'i nerede?

SDK, modelleri **uygulama adına göre ayrı** bir klasöre indirir:

```
C:\Users\<kullanici>\.FoundryLocalRAG\cache\models\
```

Bu klasör `foundry` CLI'ın kendi cache'inden **ayrıdır** — `foundry cache list`
bu modelleri göstermez ve aynı model iki kez inebilir. Klasör adı
`config.APP_NAME` değerinden gelir.

Yer açmak için kullanılmayan model klasörlerini doğrudan silebilirsiniz; eksik
model bir sonraki çalıştırmada yeniden iner.

## Kullanım

```bash
# Ortam ve model kontrolü
python main.py check

# corpus/ klasöründeki belgeleri veritabanına yükle
python main.py ingest

# Tek soru
python main.py ask "Yıllık izin kaç gün önceden istenir?"

# Soru-cevap döngüsü
python main.py chat

# Veritabanında ne var
python main.py status
```

Belge eklemek için `corpus/` klasörüne `.md`, `.txt` veya `.docx` dosyası koyup
`python main.py ingest` çalıştırmanız yeterli. Ingest **idempotent**tir: aynı dosya
tekrar işlenirse kayıtlar çoğalmaz, güncellenir; belge kısaldıysa artık karşılığı
olmayan eski parçalar silinir.

## Testler

```bash
# Hızlı testler (model gerekmez, ~0.1 sn)  -> 46 test
pytest

# Gerçek modelle uçtan uca değerlendirme (~20 sn)  -> 13 test
set FOUNDRY_RAG_E2E=1
pytest -m model -v
```

Hızlı testler sahte bir istemciyle çalışır ve chunk'lama / veri katmanı / benzerlik /
prompt kurgusunu sınar. `-m model` testleri ise sahte istemcinin gizleyebileceği şeyi
ölçer: gerçek embedding'lerle doğru parça geliyor mu, gerçek model belge dışına çıkıyor mu.
Değerlendirme setinde **kasıtlı olarak cevaplanamaz sorular** vardır; model bunlara
cevap uydurursa test kırmızı olur.

## Yapı

```
main.py                    CLI
src/foundry_rag/
  config.py                ayarlar (ortam değişkeniyle ezilebilir)
  client.py                Foundry Local: model indirme/yükleme, chat, embedding
  chunking.py              belge okuma (.md/.txt/.docx) ve parçalama
  db.py                    SQLite: chunk metni + float32 embedding BLOB
  retrieval.py             kosinüs benzerliği, top-K, eşik
  ingest.py                belge -> parça -> vektör -> veritabanı
  rag.py                   prompt kurgusu ve answer_query
tools/model_kiyas.py       sohbet modellerini aynı sorularla kıyaslar
corpus/                    kaynak belgeler
data/rag.db                üretilen veritabanı (git'e girmez)
tests/                     pytest
```

## Ölçülen sonuçlar

49 chunk'lık gerçek corpus üzerinde (RTX 4060, CUDA):

| Ölçüm | Sonuç |
|---|---|
| Yanıt süresi (uçtan uca test) | 1.32 sn |
| Yanıt süresi (gerçek corpus, uzun cevap) | 2.1 - 4.1 sn |
| Eşik altı soru (model hiç çağrılmaz) | ~0.0 sn |
| Embedding boyutu | 1024 |
| Konuyla ilgili parça benzerliği | 0.39 - 0.57 |
| Alakasız soruda en iyi parça | 0.30 - 0.31 |

## Ayarlar

| Ortam değişkeni | Varsayılan | Ne işe yarar |
|---|---|---|
| `FOUNDRY_RAG_CHAT_MODEL` | `ministral-3-3b-instruct-2512` | sohbet modeli |
| `FOUNDRY_RAG_EMBED_MODEL` | `qwen3-embedding-0.6b` | embedding modeli |
| `FOUNDRY_RAG_CORPUS` | `corpus/` | belge klasörü |
| `FOUNDRY_RAG_DB` | `data/rag.db` | veritabanı yolu |
| `FOUNDRY_RAG_E2E` | (kapalı) | `1` ise model gerektiren testler çalışır |

Chunk boyutu, `TOP_K` ve `MIN_SIMILARITY` `src/foundry_rag/config.py` içindedir ve
ortam değişkeniyle de ezilebilir (`FOUNDRY_RAG_CHUNK_CHARS`, `FOUNDRY_RAG_CHUNK_OVERLAP`,
`FOUNDRY_RAG_TOP_K`) — kıyas yapmak için. **Chunk ayarını değiştirdikten sonra
`python main.py ingest --reset` çalıştırmak gerekir.**

## Doğruluk ölçümü

```bash
python tools/degerlendirme.py
```

11 soruluk set: cevaplanabilir sorularda cevapta bulunması gereken anahtarlar
kontrol edilir, cevaplanamaz sorularda "bilmiyorum" beklenir. Sadece "bilmiyorum
dedi mi" diye bakmak yetmez — yanlış belgeden uydurulmuş bir cevap da
"bilmiyorum değil" olduğu için doğru sanılır.

Ölçülen sonuçlar (chunk boyutuna göre):

| chunk | parça | doğru | ortalama süre |
|---|---|---|---|
| 1200 | 52 | 7/11 | 2.1 sn |
| 500 | 141 | 8/11 | 2.0 sn |
| **300** | **228** | **10/11** | **1.9 sn** |

`corpus/bulut_bilisim_hafta7.md` bu setin dayandığı örnek ders notudur; kendi
belgelerinizle çalışırken silebilirsiniz (o zaman `tools/degerlendirme.py`
içindeki soruları da kendi belgelerinize göre yazın).
