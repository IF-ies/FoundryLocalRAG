# FoundryLocalRAG — Lokal RAG Belge Q&A Asistanı (Seviye 1 / Başlangıç)

> **Durum:** Faz 0-7 uygulandı (28 Ağustos 2026). Aşağıdaki kutular ölçülerek işaretlendi.
> **Amaç:** Microsoft Foundry Local + RAG ile tek makinede, tamamen **offline** çalışan belge Q&A asistanı. Belgelerden kaynak-temelli cevap üretir; internet gerekmez.
> **Kaynak:** `Summer School Foundry Local Plan.docx` (Microsoft Tech Community "Local RAG with Foundry Local" örneği).
> **Not:** Bu, **Seviye 2 (IF-ies_PrivateAI — kurumsal ürün)** için temel/PoC katmanıdır.
> **Disiplin:** Her faz sonunda commit + push (checkpoint).

---

## 1. Özet & Hedefler

- 🎯 Belgelerden (kurs notları, kılavuzlar, SSS) **kaynak-temelli** cevap veren offline chatbot
- 🎯 **RAG** (Retrieve → Augment → Generate): ilgili içeriği getir, prompt'a ekle, LLM cevap üretsin → daha az halüsinasyon
- 🎯 **Foundry Local** ile on-device LLM — bulut/GPU/internet yok
- 🎯 RAG, embeddings, vektör arama, SQLite, prompt engineering temellerini uçtan uca uygulamak

---

## 2. Teknoloji Yığını

| Katman | Seçim | Not |
|---|---|---|
| LLM runtime | **Microsoft Foundry Local** 0.10.3 + SDK 1.2.4 | On-device, offline; CUDA/DirectML/CPU |
| Chat modeli | **ministral-3-3b-instruct-2512** (3.6 GB) | 6 aday ölçülüp seçildi |
| Embedding | **qwen3-embedding-0.6b** (478 MB) | 1024 boyut, CUDA varyantı |
| Veri katmanı | **SQLite** (tek dosya) | Chunk metni + float32 embedding BLOB |
| Arama | Python'da **cosine similarity** (brute-force) | Küçük N için yeterli |
| Dil / Ortam | Python 3.13 + venv | `main.py`, `requirements.txt` |
| Arayüz | **CLI** (`check/ingest/ask/chat/status`) | |

---

## 3. Mimari

```
Kullanıcı sorusu
     │
     ▼
[Retrieval] sorguyu embed et → SQLite'taki chunk vektörleriyle cosine similarity → top-K chunk
     │        (eşiği geçen chunk yoksa modele HİÇ gitmeden "bilmiyorum")
     ▼
[Augment] soru + getirilen bağlam → prompt
     │
     ▼
[Generate] Foundry Local chat model → kaynak-temelli cevap
     │
     ▼
Kullanıcıya cevap  (hepsi tek makinede, internetsiz)
```

---

## 4. Fazlar

### Faz 0 — Ortam & İskelet
- [x] Foundry Local kurulumu (`winget install Microsoft.FoundryLocal` → 0.10.3)
- [x] Katalog doğrulaması: aday modeller GERÇEKTEN var (`foundry model list`)
- [x] Execution provider'lar indirildi (CUDA / WebGPU / OpenVINO / TensorRT-RTX)
- [x] "Hello Model" testi: `python main.py check`
- [x] Proje klasörü, `main.py`, `requirements.txt`, venv
- [x] Git repo init + private GitHub + ilk push
- [x] **Checkpoint: commit + push**

### Faz 1 — Embeddings & Vektör Arama
- [x] Foundry Local ile embedding üretimi (`client.embed` / `embed_one`)
- [x] Cosine similarity (`retrieval.cosine_similarity`)
- [x] `rank(query_vector, chunks)` — en yakın metinleri bulma
- [x] **Checkpoint: commit + push**

### Faz 2 — SQLite Veri Katmanı
- [x] `documents` tablosu (id, source, chunk_index, content, embedding, dim)
- [x] `sqlite3` ile insert/query, `(source, chunk_index)` üzerinde UNIQUE + upsert
- [x] Embedding float32 BLOB olarak saklanır; yaz→oku turu testle doğrulandı
- [x] **Checkpoint: commit + push**

### Faz 3 — Ingestion Pipeline
- [x] Belge okuma: `.md`, `.txt`, `.docx`
- [x] Paragraf sınırında chunk'lama + overlap; hiçbir chunk sınırı aşmaz
- [x] Her chunk embed edilip SQLite'a yazılır (toplu, 16'lık gruplar)
- [x] Idempotent: tekrar çalışınca kayıt çoğalmaz; belge kısalırsa artık parçalar silinir
- [x] Doğrulama: `python main.py status` ile kayıt sayısı
- [x] **Checkpoint: commit + push**

### Faz 4 — Retrieval Fonksiyonu
- [x] `rank(...)` — top-K en ilgili chunk
- [x] SQLite'tan vektörleri oku, cosine similarity, sırala
- [x] `MIN_SIMILARITY` eşiği: altında kalan her şey elenir
- [x] **Checkpoint: commit + push**

### Faz 5 — LLM Entegrasyonu
- [x] Foundry Local model yükleme (`FoundryClient`)
- [x] `answer_query(...)`: retrieval + prompt + model çağrısı
- [x] System prompt: "sadece verilen bağlamı kullan, bilmiyorsan söyle, kaynak belirt"
- [x] Bağlam boşsa model hiç çağrılmaz — doğrudan "bilmiyorum"
- [x] **Checkpoint: commit + push**

### Faz 6 — Arayüz
- [x] CLI: `check`, `ingest`, `ask`, `chat`, `status`
- [x] `chat` — çoklu soru-cevap döngüsü
- [x] Getirilen chunk'lar skoruyla birlikte gösterilir (retrieval doğrulaması)
- [ ] (Opsiyonel) Streamlit/Gradio web arayüzü — bilinçli olarak yapılmadı, CLI yeterli
- [x] **Checkpoint: commit + push**

### Faz 7 — Test & Dokümantasyon
- [x] Hızlı testler (model gerekmez): chunk'lama, DB, benzerlik, prompt, ingest
- [x] Değerlendirme seti: cevaplanabilir + **kasıtlı cevaplanamaz** sorular (`-m model`)
- [x] Edge case: boş sorgu, çok genel soru, boş veritabanı
- [x] Model kıyası (`tools/model_kiyas.py`) — 6 aday aynı sorularla ölçüldü
- [x] `MIN_SIMILARITY` gerçek corpus skorlarıyla ölçülüp 0.30 → 0.35 yapıldı
- [x] Yanıt süresi ölçümü: **1.32 sn** (e2e testi), gerçek corpus'ta 2.1-4.1 sn
- [x] README (amaç, kurulum, çalıştırma)
- [x] **Checkpoint: commit + push**

---

## 4.5 Azure'un Rolü (dev aracı — üretim lokal kalır)

> Sağlanan **Azure hesabı** bu seviyede yalnızca **geliştirme/model-katalog aracı**dır. Çalışan ürün **tamamen Foundry Local** ile lokal/offline kalır — "gizli & lokal" ilkesi korunur.

- **Model keşfi & kıyas:** Azure AI Foundry portalinden modelleri (Phi, Qwen vb.) incele/dene, en uygununu seç → **Foundry Local'e alıp lokal çalıştır**
- **Ağır ön-işleme (opsiyonel):** Büyük belge setlerinin ilk embedding üretimi/denemeleri geliştirme sırasında Azure'da hızlandırılabilir; **üretim verisi Azure'a gönderilmez**
- **Sınır:** Son kullanıcı çalışması sırasında **hiçbir çağrı buluta gitmez** (offline garanti)

**Uygulamada:** Seviye 1'de Azure'a hiç ihtiyaç duyulmadı. Model kataloğu Foundry Local'in
kendi `foundry model list` çıktısından okundu, indirme Microsoft'un genel kataloğundan
yapıldı — Azure aboneliği devreye girmedi, ücret oluşmadı.

---

## 5. Başarı Kriterleri

Hepsi ölçülerek doğrulandı (49 chunk'lık gerçek corpus + 13 uçtan uca test):

- ✅ İnternetsiz çalışır (modeller indirildikten sonra)
- ✅ Belge havuzunda olan soruya **kaynak-temelli doğru** cevap verir
- ✅ Bilgi yoksa **"bilmiyorum"** der — eşiği geçen parça yoksa model hiç çağrılmaz
- ✅ Yanıt süresi **1.32 sn** (hedef 1-3 sn), gerçek corpus'ta 2.1-4.1 sn

## 6. Öğrenilenler

- **Planın model varsayımları doğruydu ama SDK'nınki değildi.** `foundry-local-sdk` 1.2.4
  ile modül adı `foundry_local` değil `foundry_local_sdk`; `FoundryLocalManager` artık
  singleton ve `Configuration(app_name=...)` alıyor; `download_model/load_model/endpoint`
  yerine `catalog.get_model(alias)` → `model.download()/load()/get_chat_client()` var.
  Ayrı HTTP sunucusu ve `openai` istemcisi gerekmiyor. **Ders: SDK API'si dokümandan değil
  kurulu paketten okunmalı.**
- **Test beklentisi de yanlış olabilir.** İlk koşuda 2 test kırmızı çıktı; ikisinde de kod
  doğru, testin senaryosu yanlıştı (90 karakterlik paragraf 100'lük sınırda overlap'e yer
  bırakmıyor; `sorted()` dosya adına değil göreli yola göre sıralıyor). Kodu teste
  uydurmak yerine gerçek davranış ölçülüp teste yazıldı.
- **Bağlam boşken modeli hiç çağırmamak**, "bilmiyorum" garantisini prompt'a güvenmekten
  çok daha sağlam kılıyor — model uydurmak istese bile elinde malzeme olmuyor.
- **Model seçimi ölçülmeden yapılamaz.** Altı aday aynı üç soruyla denendi
  (`tools/model_kiyas.py`) ve hiçbirini kâğıt üzerinden tahmin edemezdik:
  `qwen3-4b` cevabın içine `<think>` bloğu sızdırıyor, `qwen3.5-2b` Türkçeyi
  bozuyor ("Zrdali", "BuBelgeleCevaplayamıyorum"), `qwen2.5-7b` doğru ama RAG'de
  8-11 sn. Kazanan `ministral-3-3b`: doğru ve 2-4 sn.
- **"Bilmiyorum" demek uydurmayı DURDURMUYOR.** `qwen2.5-1.5b` ölçümde
  "cevaplayamıyorum" dedi ve hemen ardından "2024 cirosu 1000 tane olacaktır"
  diye rakam uydurdu. Tespit doğru çalışıyordu ama kullanıcı uydurma kuyruğu
  okuyordu. Artık cevap "bilmiyorum" ise metin sabit ifadeye indiriliyor.
- **Cevabın tam metnini aramak kırılgan.** `is_unknown` başta birebir eşitlik
  arıyordu; `phi-3.5-mini` "cevaplamadım" deyince tespit kaçıyordu. Artık
  ifadenin değişmeyen çekirdeği (`UNKNOWN_MARKER`) aranıyor.
- **Model kaynakça da uydurabiliyor.** İlk denemede cevabın altına
  `https://belge-sayfası-1` gibi sahte bağlantılar yazdı; prompt'a "yalnızca
  bağlamdaki dosya adları, URL uydurma" kuralı eklendi.
- **Aşırı temkin de bir hata.** İlk sıkı prompt ile model, bağlamda bilgi
  olduğu hâlde "cevaplayamıyorum" diyordu. "Kısmen cevaplıyorsa cevaplayabildiğin
  kadarını ver" kuralı eklenince yanlış negatif kalktı, cevaplanamaz sorular
  yine "bilmiyorum" demeye devam etti (13/13 e2e testi geçiyor).
- **Diakritiksiz Türkçe küçük modelleri bozuyor.** `check` komutunda soru
  "Turkiye'nin baskenti" diye ASCII yazılınca `phi-3.5-mini` anlamsız tekrar
  döngüsüne girdi; düzgün Türkçeyle aynı model "Ankara" dedi.

## 7. Sonraki Adım
- Gerçek ders notlarını `corpus/` klasörüne koyup tekrar `ingest` (seçenek **a**)
- Ardından → **Seviye 2: `IF-ies_PrivateAI`** (çok kullanıcılı, rol bazlı, on-prem kurumsal ürün)
