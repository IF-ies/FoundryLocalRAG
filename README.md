# FoundryLocalRAG

Microsoft **Foundry Local** üzerinde çalışan, **tamamen offline** belge soru-cevap asistanı.
Belgelerinizi okur, sorularınızı yalnızca o belgelere dayanarak cevaplar, bilmediğinde
"bilmiyorum" der. Hiçbir veri makineden çıkmaz.

> Bu depo, kurumsal sürüm olan **IF-ies_PrivateAI**'ın temel (PoC) katmanıdır.

<details>
<summary><b>In English</b></summary>

A fully offline document question-answering assistant built on **Microsoft Foundry
Local**. It reads your documents, answers only from them, and says "I don't know"
when the answer isn't there. No data ever leaves the machine — no cloud, no API key.

Stack: Foundry Local (ONNX) · `ministral-3-3b` for chat · `qwen3-embedding-0.6b`
for embeddings · SQLite with float32 embedding blobs · brute-force cosine similarity.
Reads `.md`, `.txt`, `.docx` and `.pdf`.

Every setting was **measured, not guessed**: the chat model was picked by comparing
six candidates on the same questions; chunk size was tuned per corpus (300 chars won
on short lecture notes, 1400 on long academic papers); `top_k=5` was tried twice and
rejected because it cost time without improving accuracy.

Current score on the built-in evaluation set: **10/13, 1.9 s average**. The remaining
three failures are retrieval misses — documented, not hidden.

Documentation is in Turkish; the code and comments are self-contained.

</details>

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
"bilmiyorum" döner — uydurmaya malzeme verilmez. Model yine de "cevaplayamıyorum"
deyip ardından uydurmaya devam ederse, cevap sabit ifadeye indirilir (ölçülmüş bir
davranış: bir model "cevaplayamıyorum" dedikten sonra rakam uydurdu).

## Kullanılan modeller

| Rol | Model | Boyut |
|---|---|---|
| Sohbet | `ministral-3-3b-instruct-2512` | 3.6 GB |
| Embedding | `qwen3-embedding-0.6b` | 478 MB |

Sohbet modeli tahminle değil **ölçülerek** seçildi: altı aday aynı Türkçe sorularla
denendi (`python tools/model_kiyas.py <alias> ...`). Elenenler ve sebepleri
`src/foundry_rag/config.py` içinde yazılıdır.

## Desteklenen belge türleri

`.md` · `.txt` · `.docx` · `.pdf`

PDF'ten yalnızca **metin katmanı** okunur — taranmış/fotoğraflanmış PDF'te metin
yoktur, OCR yapılmaz; ingest böyle dosyaları atlayıp raporlar.

PDF'in gömülü font subset'i çözülemediğinde çıkarım `/gid00047` gibi okunamaz glif
kodları üretir. Böyle parçalar ingest sırasında **elenir ve raporlanır** (mevcut
corpus'ta 807 parçanın 11'i). Sayı yoğun parçalar (tablolar, ölçüm sonuçları)
bilerek elenmez — içlerinde gerçek cevap olabilir.

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
`config.APP_NAME` değerinden gelir. Yer açmak için kullanılmayan model
klasörlerini doğrudan silebilirsiniz; eksik model bir sonraki çalıştırmada
yeniden iner.

## Kullanım

PowerShell'de en kolayı başlatıcıyı kullanmaktır (venv'deki Python'u seçer ve
Türkçe için çıktı kodlamasını ayarlar):

```powershell
.
ag.ps1                            # doğrudan sohbet
.
ag.ps1 ask "sorunuz"
.
ag.ps1 ingest --reset
.
ag.ps1 status
```

Başlatıcısız eşdeğeri:

```bash
python main.py check                 # ortam ve model kontrolü
python main.py ingest                # corpus/ klasörünü veritabanına yükle
python main.py ingest --reset        # önce veritabanını temizleyerek yükle
python main.py ask "sorunuz"         # tek soru
python main.py chat                  # soru-cevap döngüsü
python main.py status                # veritabanında ne var
```

Belge eklemek için `corpus/` klasörüne dosya koyup `ingest` çalıştırmanız yeterli.
Ingest **idempotent**tir: aynı dosya tekrar işlenirse kayıtlar çoğalmaz, güncellenir;
belge kısaldıysa artık karşılığı olmayan eski parçalar silinir.

## Mevcut corpus: yapay zekâ felsefesi

`corpus/` klasöründe, birbiriyle **çelişen** görüşleri temsil eden altı güncel arXiv
makalesi vardır (bilinç, ahlaki statü, yapay kişilik, değer uyumu, AGI'nin
tanımlanabilirliği ve bu tanımların eleştirisi). Künye, özetler ve indirme komutları
[`KAYNAKLAR.md`](KAYNAKLAR.md) dosyasındadır.

PDF'ler git'e girmez (telif + boyut); `KAYNAKLAR.md` yeniden indirme komutlarını tutar.

## Testler

```bash
# Hızlı testler (model gerekmez, ~0.1 sn)  -> 49 test
pytest

# Gerçek modelle uçtan uca değerlendirme (~16 sn)  -> 13 test
set FOUNDRY_RAG_E2E=1
pytest -m model -v
```

Hızlı testler sahte bir istemciyle çalışır ve chunk'lama / veri katmanı / benzerlik /
prompt kurgusunu sınar. `-m model` testleri ise sahte istemcinin gizleyebileceği şeyi
ölçer: gerçek embedding'lerle doğru parça geliyor mu, gerçek model belge dışına çıkıyor mu.
Değerlendirme setinde **kasıtlı olarak cevaplanamaz sorular** vardır; model bunlara
cevap uydurursa test kırmızı olur.

## Doğruluk ölçümü

```bash
python tools/degerlendirme.py
```

13 soruluk set: cevaplanabilir sorularda cevapta bulunması gereken anahtarlar
kontrol edilir, cevaplanamaz sorularda "bilmiyorum" beklenir. Sadece "bilmiyorum
dedi mi" diye bakmak **yetmez** — yanlış belgeden uydurulmuş bir cevap da
"bilmiyorum değil" olduğu için doğru sanılır.

Sorular Türkçe, belgeler İngilizce — bu kasıtlı; anahtarlar `|` ile her iki dilde
alternatif içerir ve Türkçe eklerini yakalasın diye köke yazılır.

**Mevcut sonuç: 10/13, ortalama 1.9 sn.** Kalan üç hata retrieval'in kaçırdığı
bilgilerdir (ilgili parça ilk üçe giremiyor).

### En iyi chunk boyutu corpus'a bağlıdır

Sabit bir doğru yoktur; **ölçmek gerekir**. İki zıt ölçüm:

| corpus | 300 | 500-600 | 1000 | 1400 | 1800 |
|---|---|---|---|---|---|
| Kısa ders notu (4 belge) | **10/11** | 8/11 | — | — | — |
| Akademik makale (6 belge) | 8/13 | 5/13 | 8/13 | **10/13** | 8/13 |

Kısa belgede küçük chunk ayrıntıyı öne çıkarır. Uzun akademik metinde argüman
bütünlüğü gerekir; binlerce küçük parça birbirine benzeyip kaybolur.

**Yeni bir belge seti koyduğunuzda:** `tools/degerlendirme.py` içindeki soruları
kendi belgelerinize göre yazın, birkaç chunk boyutu deneyin, en iyisini
`config.py`'ye yazın.

## Yapı

```
main.py                    CLI
src/foundry_rag/
  config.py                ayarlar (ortam değişkeniyle ezilebilir)
  client.py                Foundry Local: model indirme/yükleme, chat, embedding
  chunking.py              belge okuma (.md/.txt/.docx/.pdf) ve parçalama
  db.py                    SQLite: chunk metni + float32 embedding BLOB
  retrieval.py             kosinüs benzerliği, top-K, eşik
  ingest.py                belge -> parça -> vektör -> veritabanı
  rag.py                   prompt kurgusu ve answer_query
tools/model_kiyas.py       sohbet modellerini aynı sorularla kıyaslar
tools/degerlendirme.py     corpus üzerinde cevap doğruluğunu ölçer
corpus/                    kaynak belgeler (PDF'ler git'e girmez)
KAYNAKLAR.md               corpus künyesi + indirme komutları
data/rag.db                üretilen veritabanı (git'e girmez)
tests/                     pytest
```

## Ayarlar

| Ortam değişkeni | Varsayılan | Ne işe yarar |
|---|---|---|
| `FOUNDRY_RAG_CHAT_MODEL` | `ministral-3-3b-instruct-2512` | sohbet modeli |
| `FOUNDRY_RAG_EMBED_MODEL` | `qwen3-embedding-0.6b` | embedding modeli |
| `FOUNDRY_RAG_CORPUS` | `corpus/` | belge klasörü |
| `FOUNDRY_RAG_DB` | `data/rag.db` | veritabanı yolu |
| `FOUNDRY_RAG_CHUNK_CHARS` | `1400` | chunk üst sınırı |
| `FOUNDRY_RAG_CHUNK_OVERLAP` | `150` | chunk'lar arası taşınan bağlam |
| `FOUNDRY_RAG_TOP_K` | `3` | bağlama alınacak parça sayısı |
| `FOUNDRY_RAG_TEMPERATURE` | `0.0` | üretim sıcaklığı |
| `FOUNDRY_RAG_E2E` | (kapalı) | `1` ise model gerektiren testler çalışır |

**Chunk ayarını değiştirdikten sonra `python main.py ingest --reset` gerekir.**

`temperature` varsayılanı 0'dır: ayar karşılaştırması yapabilmek için üretimin
tekrarlanabilir olması gerekiyor. 0.2'de aynı ayarla yapılan koşuların aynı sonucu
verdiğinden emin olunamıyordu; 0.0'da iki koşu birebir aynı çıkıyor.

## Lisans

[MIT](LICENSE) — kullanabilir, değiştirebilir, dağıtabilirsiniz; telif satırını koruyun.

Not: `corpus/` klasöründeki makalelerin telifi kendi yazarlarına aittir ve bu depoya
dahil edilmemiştir; [`KAYNAKLAR.md`](KAYNAKLAR.md) yalnızca künyeyi ve indirme
komutlarını içerir.
