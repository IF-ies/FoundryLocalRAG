# IF-ies PrivateAI — Kurumsal Gizli & Lokal AI (Seviye 2 / Üst Seviye)

> **Durum:** Planlama aşaması — kod henüz yazılmadı.
> **Amaç:** `FoundryLocalRAG` (Seviye 1) temelinin üstüne kurulan; şirket ortamına **on-prem** kurulan, veri şirketten **hiç çıkmayan** (KVKK/GDPR), **çok kullanıcılı**, **rol/departman bazlı** kurumsal gizli AI ürünü.
> **Önkoşul:** Seviye 1 (`C:\Github_Repo\FoundryLocalRAG`) çekirdeği çalışıyor olmalı.
> **Disiplin:** Her faz sonunda commit + push (checkpoint).

---

## 1. Özet & Hedefler

- 🎯 Şirket belgelerinden (sözleşme, prosedür, İK, teknik doküman) **kaynak-temelli** cevap veren özel asistan
- 🎯 **Veri egemenliği:** hiçbir veri buluta/internete çıkmaz — air-gapped çalışabilir
- 🎯 **Çok kullanıcılı + RBAC:** kullanıcı yalnızca yetkili olduğu belgelerden cevap alır (retrieval seviyesinde izin)
- 🎯 **Türkçe + çok dilli**; kurumsal sistemlere API ile entegrasyon
- 🎯 **Satılabilir ürün:** Docker ile şirket sunucusuna kurulum, admin paneli, denetim

**Satış argümanı:** Sopyo/ChatGPT Enterprise'ın aksine veri şirket dışına çıkmaz — hukuk, sağlık, finans, savunma gibi gizlilik-kritik sektörler için.

---

## 2. Seviye 1'e Göre Yükseltmeler

| Konu | Seviye 1 | Seviye 2 (bu proje) |
|---|---|---|
| Vektör store | brute-force cosine | **sqlite-vec** (ANN, tek dosya) → ölçekte **Qdrant** |
| Embedding | qwen3-embedding | **bge-m3** (çok dilli/Türkçe) + **bge-reranker-v2-m3** |
| Arama | sadece vektör | **hibrit** (BM25 + vektör + reranker) |
| LLM | Phi-3.5 | **Qwen2.5** (Türkçe yetkin), Ollama fallback |
| Belge tipi | düz metin | **PDF/DOCX/XLSX/PPTX/HTML/e-posta** + artımlı indeks |
| Kullanıcı | tek | **çok kullanıcı + RBAC + departman izni** |
| Arayüz | CLI | **Web sohbet + admin panel** |
| Entegrasyon | yok | **OpenAI-uyumlu REST API** |
| Güvenlik | yok | audit log, at-rest şifreleme, air-gapped, guardrails |

---

## 3. Teknoloji Yığını

| Katman | Seçim |
|---|---|
| Backend/API | **FastAPI** (OpenAI-uyumlu endpoint dahil) |
| Metadata DB | **PostgreSQL** (kullanıcı, rol, belge metadata, audit) |
| Vektör DB | **sqlite-vec** (başlangıç) → **Qdrant** (ölçek) |
| Embedding | **bge-m3** + reranker **bge-reranker-v2-m3** |
| LLM | **Qwen2.5** (Foundry Local / Ollama) |
| Web UI | React veya HTMX (sohbet + admin) |
| Dağıtım | **Docker Compose**, air-gapped |
| Dil/Ortam | Python 3.11+ |

---

## 4. Mimari

```
[Kullanıcı: Web / API]  ──►  Auth + RBAC (kimlik, rol, departman)
                                     │
                                     ▼
                        Sorgu ──► hibrit arama (BM25 + bge-m3 vektör)
                                     │  ▲ izin filtresi (sadece yetkili belgeler)
                                     ▼
                            reranker (bge-reranker) → top-K chunk
                                     │
                         Augment (bağlam + guardrail prompt)
                                     │
                            LLM (Qwen2.5 / Foundry Local)
                                     │
                     Kaynak atıflı cevap  +  Audit log

[Admin panel] ──► belge yükle/indeksle, kullanıcı/rol/departman yönetimi
```
- **Tümü on-prem, air-gapped çalışabilir.** Veri şirket sunucusundan çıkmaz.

---

## 5. Fazlar

### Faz 0 — Kurumsal İskelet
- [ ] FastAPI + PostgreSQL + sqlite-vec, Docker Compose
- [ ] Config sistemi (model, DB, gizli anahtarlar, port)
- [ ] Repo + private GitHub + ilk push
- [ ] **Checkpoint: commit + push**

### Faz 1 — Gelişmiş Ingestion
- [ ] Çok formatlı parser: PDF, DOCX, XLSX, PPTX, HTML, e-posta
- [ ] Akıllı chunk'lama (yapı-farkında, overlap) + metadata (kaynak, departman, tarih)
- [ ] Artımlı yeniden indeksleme (değişen belge tespiti, hash)
- [ ] **Checkpoint: commit + push**

### Faz 2 — Çok Dilli Arama
- [ ] bge-m3 embedding entegrasyonu (Türkçe/çok dilli)
- [ ] Hibrit arama: BM25 (anahtar kelime) + vektör
- [ ] bge-reranker-v2-m3 ile yeniden sıralama
- [ ] **Checkpoint: commit + push**

### Faz 3 — Kimlik & RBAC
- [ ] Kullanıcı/rol/departman modeli (Postgres)
- [ ] Auth (JWT; opsiyonel LDAP/SSO)
- [ ] **Retrieval-seviyesi izin filtreleme** (kullanıcı sadece yetkili belgelerden cevap alır)
- [ ] **Checkpoint: commit + push**

### Faz 4 — RAG Çekirdeği + Guardrails
- [ ] Soyut `LLMProvider` arayüzü: `LocalProvider` (Foundry Local/Ollama) + opsiyonel `AzureFoundryProvider` (bulut tier, config ile aç/kapa)
- [ ] Qwen2.5 ile RAG cevap üretimi (lokal varsayılan)
- [ ] Kaynak atıfı (hangi belge/sayfa), "bilmiyorum" fallback
- [ ] Prompt-injection savunması (belge içi kötü niyetli talimat filtresi)
- [ ] **Checkpoint: commit + push**

### Faz 5 — Web UI
- [ ] Sohbet arayüzü (kaynak gösterimi, oturum geçmişi)
- [ ] Admin paneli: belge yükleme/indeksleme durumu, kullanıcı/rol/departman yönetimi
- [ ] **Checkpoint: commit + push**

### Faz 6 — API & Entegrasyon
- [ ] OpenAI-uyumlu REST API (mevcut araçlara kolay bağlanma)
- [ ] Webhook / kurumsal sistem entegrasyon noktaları
- [ ] API anahtarı/oran sınırlama
- [ ] **Checkpoint: commit + push**

### Faz 7 — Denetim, Gözlemlenebilirlik & Değerlendirme
- [ ] Audit log (kim, ne sordu, hangi belgeler getirildi)
- [ ] Metrikler (yanıt süresi, retrieval kalitesi)
- [ ] **ragas** ile RAG doğruluk değerlendirmesi
- [ ] **Checkpoint: commit + push**

### Faz 8 — On-prem Dağıtım & Paketleme
- [ ] Docker imajları + air-gapped kurulum rehberi (model önceden indirilmiş)
- [ ] Lisanslama / sürüm yönetimi
- [ ] Yedekleme & geri yükleme
- [ ] **Checkpoint: commit + push**

### Faz 9 (Opsiyonel) — Ölçek
- [ ] Çoklu departman/tenant (izole bilgi tabanları)
- [ ] sqlite-vec → Qdrant geçişi
- [ ] Yük dengeleme, çoklu worker
- [ ] **Checkpoint: commit + push**

---

## 5.5 Azure'un Rolü (dev aracı + opsiyonel bulut tier)

> Sağlanan **Azure hesabı** iki yerde kullanılır. **Varsayılan ürün on-prem/air-gapped kalır** (satış argümanı bozulmaz); Azure bulut yalnızca **müşteri açıkça isterse** opt-in devreye girer.

**A) Geliştirme & model-katalog aracı (her müşteride):**
- Azure AI Foundry portalinden model keşfi/kıyas → seçileni **Foundry Local / Ollama'ya alıp on-prem** çalıştır
- Geliştirme/CI ortamı, ağır ön-işleme, embedding deneyleri (üretim verisi gitmeden)

**B) Opsiyonel "Bulut Tier" (soyut `LLMProvider` ile):**
- `LLMProvider` arayüzü: `LocalProvider` (Foundry Local/Ollama) **veya** `AzureFoundryProvider` (Azure AI Foundry cloud)
- Bulut isteyen müşteri daha büyük/güçlü modele erişir; **air-gapped garantisinden feragat eder** → sözleşmede net belirtilir
- Aynı kod tabanı, tek config anahtarıyla lokal ↔ bulut geçişi

**⚠️ Uyarı:** Bulut tier açıldığında veri Azure'a gider → "veri şirketten çıkmaz" garantisi **o müşteri için geçersiz**. Bu yüzden **varsayılan kapalı**, KVKK/gizlilik-kritik müşterilerde **hiç açılmaz**.

---

## 6. Güvenlik & Uyum

- **Veri egemenliği:** Tüm veri/işlem on-prem; air-gapped çalışabilir, buluta hiçbir şey gitmez
- **KVKK / GDPR:** Kişisel veri şirket sınırlarında kalır, silme/erişim hakları
- **RBAC:** Belge/departman bazlı erişim, retrieval seviyesinde uygulanır
- **At-rest şifreleme** + tam **audit log**
- **Guardrails:** kaynak atıfı, "bilmiyorum", prompt-injection savunması

---

## 7. Başarı Kriterleri

- ✅ Şirket sunucusuna Docker ile kurulur, internetsiz çalışır
- ✅ Kullanıcı **sadece yetkili** belgelerden cevap alır (izin sızıntısı yok)
- ✅ Türkçe belge/soruda kaliteli, **kaynaklı** cevap
- ✅ Her sorgu **denetlenebilir** (audit log)
