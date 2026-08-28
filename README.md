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
| Sohbet | `phi-3.5-mini` | 2.1 GB |
| Embedding | `qwen3-embedding-0.6b` | 478 MB |

Foundry Local donanıma uygun varyantı kendisi seçer (CUDA GPU varsa onu kullanır).
Model değiştirmek için kod düzenlemeye gerek yok:

```bash
set FOUNDRY_RAG_CHAT_MODEL=qwen3-4b
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
# Hızlı testler (model gerekmez, saniyeler sürer)
pytest

# Gerçek modelle uçtan uca değerlendirme (yavaş)
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
corpus/                    kaynak belgeler
data/rag.db                üretilen veritabanı (git'e girmez)
tests/                     pytest
```

## Ayarlar

| Ortam değişkeni | Varsayılan | Ne işe yarar |
|---|---|---|
| `FOUNDRY_RAG_CHAT_MODEL` | `phi-3.5-mini` | sohbet modeli |
| `FOUNDRY_RAG_EMBED_MODEL` | `qwen3-embedding-0.6b` | embedding modeli |
| `FOUNDRY_RAG_CORPUS` | `corpus/` | belge klasörü |
| `FOUNDRY_RAG_DB` | `data/rag.db` | veritabanı yolu |
| `FOUNDRY_RAG_E2E` | (kapalı) | `1` ise model gerektiren testler çalışır |

Chunk boyutu, `TOP_K` ve `MIN_SIMILARITY` gibi ayarlar `src/foundry_rag/config.py`
içindedir.
