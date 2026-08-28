# FoundryLocalRAG — Lokal RAG Belge Q&A Asistanı (Seviye 1 / Başlangıç)

> **Durum:** Planlama aşaması — kod henüz yazılmadı.
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
| LLM runtime | **Microsoft Foundry Local** (Python SDK) | On-device, offline, CPU/NPU hızlandırma |
| Chat modeli | **Phi-3.5 Mini** / Qwen2.5 3B | Küçük = hızlı geri bildirim |
| Embedding | **qwen3-embedding-0.6b** (Foundry Local) | Metin → vektör |
| Veri katmanı | **SQLite** (tek dosya) | Belge metni + embedding saklama |
| Arama | Python'da **cosine similarity** (brute-force) | Küçük N için yeterli |
| Dil / Ortam | Python 3.11+, venv | `main.py`, `requirements.txt` |
| Arayüz | **CLI** (birincil), opsiyonel Streamlit/Gradio | |

---

## 3. Mimari

```
Kullanıcı sorusu
     │
     ▼
[Retrieval] sorguyu embed et → SQLite'taki chunk vektörleriyle cosine similarity → top-K chunk
     │
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
- [ ] Foundry Local SDK kurulumu (Windows + macOS test)
- [ ] "Hello Model" testi: küçük modelle basit completion (runtime çalışıyor mu)
- [ ] Proje klasörü, `main.py` (entry point), `requirements.txt`
- [ ] Git repo init + private GitHub + ilk push
- [ ] **Checkpoint: commit + push**

### Faz 1 — Embeddings & Vektör Arama
- [ ] Örnek cümleler için Foundry Local ile embedding üretimi
- [ ] Cosine similarity hesaplama
- [ ] `find_relevant(query)` — sorguya en yakın metni bulma
- [ ] **Checkpoint: commit + push**

### Faz 2 — SQLite Veri Katmanı
- [ ] `documents` tablosu (id, content, embedding)
- [ ] `sqlite3` ile insert/query
- [ ] Embedding'i BLOB / JSON-serialized vektör olarak saklama-okuma
- [ ] **Checkpoint: commit + push**

### Faz 3 — Ingestion Pipeline
- [ ] 5-10 belge seç (kurs notu / SSS / kılavuz)
- [ ] Belgeleri chunk'lama (paragraf/başlık, ~1-3 paragraf)
- [ ] Her chunk'ı embed et + SQLite'a yaz
- [ ] Doğrulama: DB'deki kayıt sayısı beklenen mi
- [ ] **Checkpoint: commit + push**

### Faz 4 — Retrieval Fonksiyonu
- [ ] `get_top_chunks(query)` — 2-3 en ilgili chunk
- [ ] SQLite'tan vektörleri oku, cosine similarity, top-K seç
- [ ] Örnek sorgularla ilgili chunk'ların döndüğünü test et
- [ ] **Checkpoint: commit + push**

### Faz 5 — LLM Entegrasyonu
- [ ] Foundry Local chat model yükleme (startup)
- [ ] `answer_query(user_question)`: retrieval + prompt + model çağrısı
- [ ] System prompt: "sadece verilen bağlamı kullan, bilmiyorsan söyle, kaynak belirt"
- [ ] Uçtan uca test (bilinen soruyla)
- [ ] **Checkpoint: commit + push**

### Faz 6 — Arayüz
- [ ] CLI: `input()` döngüsü ile çoklu soru-cevap
- [ ] (Opsiyonel) Streamlit/Gradio minimal web arayüzü
- [ ] Getirilen chunk'ları loglama (retrieval doğrulaması)
- [ ] **Checkpoint: commit + push**

### Faz 7 — Test & Dokümantasyon
- [ ] Test soruları: cevaplanabilir + cevaplanamaz (fallback "bilmiyorum" testi)
- [ ] Edge case: boş sorgu, çok genel soru
- [ ] Yanıt süresi ölçümü (~1-3 sn hedef)
- [ ] README (amaç, kurulum, çalıştırma) + demo hazırlığı
- [ ] **Checkpoint: commit + push**

---

## 4.5 Azure'un Rolü (dev aracı — üretim lokal kalır)

> Sağlanan **Azure hesabı** bu seviyede yalnızca **geliştirme/model-katalog aracı**dır. Çalışan ürün **tamamen Foundry Local** ile lokal/offline kalır — "gizli & lokal" ilkesi korunur.

- **Model keşfi & kıyas:** Azure AI Foundry portalinden modelleri (Phi, Qwen vb.) incele/dene, en uygununu seç → **Foundry Local'e alıp lokal çalıştır**
- **Ağır ön-işleme (opsiyonel):** Büyük belge setlerinin ilk embedding üretimi/denemeleri geliştirme sırasında Azure'da hızlandırılabilir; **üretim verisi Azure'a gönderilmez**
- **Sınır:** Son kullanıcı çalışması sırasında **hiçbir çağrı buluta gitmez** (offline garanti)

---

## 5. Başarı Kriterleri

- ✅ İnternetsiz çalışır (offline)
- ✅ Belge havuzunda olan soruya **kaynak-temelli doğru** cevap verir
- ✅ Bilgi yoksa **"bilmiyorum"** der (halüsinasyon yok)
- ✅ Yanıt süresi tipik laptopta makul (~1-3 sn)

## 6. Sonraki Adım
Bu tamamlandığında → **Seviye 2: `IF-ies_PrivateAI`** (çok kullanıcılı, rol bazlı, on-prem kurumsal ürün) fazlarına geçilir.
