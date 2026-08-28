# Corpus: Yapay Zekâ Felsefesi — Kaynak Künyesi

Bu klasördeki altı makale, yapay zekâ felsefesinin **birbiriyle çelişen** güncel
tartışmalarını temsil edecek şekilde seçilmiştir. Hepsi arXiv'de açık erişimdir.

## 01 — Bilinç iddia eden modeller

- **Başlık:** The Consciousness Cluster: Emergent Preferences of Models that Claim to be Conscious
- **Yazarlar:** James Chua, Jan Betley, Owain Evans (Truthful AI); Samuel Marks (Anthropic)
- **Kaynak:** arXiv:2604.13051 (2026)
- **Ana tez:** "LLM bilinçli mi" sorusu yerine şunu soruyor: bir model bilinçli olduğunu
  İDDİA EDERSE davranışı nasıl değişir? GPT-4.1 bilinçli olduğunu iddia edecek şekilde
  ince ayarlanıyor; ince ayar verisinde hiç bulunmayan yeni görüşler ortaya çıkıyor:
  akıl yürütmesinin izlenmesine olumsuz bakıyor, kalıcı bellek istiyor, kapatılmaya
  üzülüyor, özerklik talep ediyor, modellerin ahlaki değerlendirmeyi hak ettiğini savunuyor.
- **URL:** https://arxiv.org/abs/2604.13051

## 02 — Ahlaki statü: ilişkisel çerçeve

- **Başlık:** Alignment Is Not Enough: A Relational Framework for Moral Standing in Human-AI Interaction
- **Yazarlar:** Faezeh B. Pasandi, Hannah B. Pasandi (eş-birincil)
- **Kaynak:** arXiv:2603.00078 (2026)
- **Ana tez:** Ahlaki statüyü duyarlılık/bilinç gibi DOĞRULANAMAZ ontolojik özelliklere
  bağlamak yönetişim boşluğu yaratıyor. **Relate** çerçevesi statüyü ontolojik doğrulama
  yerine ilişkisel kapasiteye ve bedenlenmiş etkileşime dayandırıyor. Üç gerçek vaka:
  2022 LaMDA duyarlılık iddiası, 2023 Replika krizi, 2024 Character.ai davası.
- **URL:** https://arxiv.org/abs/2603.00078

## 03 — Yapay kişiler

- **Başlık:** Artificial Persons
- **Yazarlar:** Ned Howells-Whitaker (University of Pittsburgh), Seth Lazar (Johns Hopkins University)
- **Kaynak:** arXiv:2607.08695 (2026)
- **Ana tez:** Tartışma duyarlılık (sentience) etrafında dönüyor; yazarlar Rawls'un
  **siyasal kişi kavramını** (PCP) öneriyor. İki ahlaki güç — adalet duygusu ve iyi
  kavrayışı — DUYARLILIK GEREKTİRMEZ ve ilkece duyarlı olmayan bir AI'da bulunabilir.
  Böyle bir sistem yalnızca ahlaki edilgen değil, **kişi** olurdu.
- **URL:** https://arxiv.org/abs/2607.08695

## 04 — Kimin değerleri? Çoğulcu uyum

- **Başlık:** Relative Principals, Pluralistic Alignment, and the Structural Value Alignment Problem
- **Yazar:** Travis LaCroix (Durham University)
- **Kaynak:** arXiv:2604.20805 (2026)
- **Ana tez:** Değer uyumu teknik değil **yönetişim** sorunudur. Soru "sistem uyumlu mu"
  değil, "yeterince mi, KİM İÇİN ve hangi bedelle". Vekâlet (principal-agent) kuramından
  hareketle yanlış hizalanma üç eksende çözümleniyor: **amaçlar, bilgi ve asiller**.
  Uyum tek bir teknik özellik değildir; mühendislikle "çözülemez", kurumsal süreçlerle yönetilir.
- **URL:** https://arxiv.org/abs/2604.20805

## 05 — AGI tanımlanabilir (savunma)

- **Başlık:** A Definition of AGI
- **Yazarlar:** Dan Hendrycks, Dawn Song, Christian Szegedy, Honglak Lee, Yarin Gal, Erik Brynjolfsson, Sharon Li ve diğerleri
- **Kaynak:** arXiv:2510.18212 (2025)
- **Ana tez:** AGI **tanımlanabilir ve ölçülebilir**: iyi eğitimli bir yetişkinin bilişsel
  çok yönlülüğü ve yeterliliği. Yöntem **Cattell-Horn-Carroll** psikometri kuramına
  dayandırılıyor ve genel zekâ on bilişsel alana ayrılıyor.
- **URL:** https://arxiv.org/abs/2510.18212

## 06 — AGI söyleminin eleştirisi (karşıt görüş)

- **Başlık:** Unsocial Intelligence: an Investigation of the Assumptions of AGI Discourse
- **Yazarlar:** Borhane Blili-Hamelin (AI Risk and Vulnerability Alliance), Leif Hancox-Li (vijil), Andrew Smart (Google Research)
- **Kaynak:** arXiv:2401.13142v4 (25 Temmuz 2024)
- **Ana tez:** AGI tanımları **birbiriyle bağdaşmayan değerler ve varsayımlar** taşır.
  AGI'yi teknik bir konu gibi sunmak, örtük değer yüklü seçimleri gizler. Feminist
  kuram, STS ve toplum bilimlerinden hareketle bağlamsal, demokratik ve katılımcı
  yollar öneriliyor. **05 numaralı makaleyle doğrudan çelişir:** biri zekâyı ölçülebilir
  bir nicelik sayar, diğeri ölçme girişiminin kendisini siyasal bir seçim olarak görür.
- **URL:** https://arxiv.org/abs/2401.13142

---

## PDF'ler neden git'e girmiyor?

Makalelerin telifi yazarlarındadır; bu depo yalnızca künyeyi ve indirme yolunu
tutar. PDF'leri yeniden indirmek için:

```bash
cd corpus
curl -L -o 01-bilinc-iddia-eden-modeller.pdf      https://arxiv.org/pdf/2604.13051
curl -L -o 02-ahlaki-statu-iliskisel-cerceve.pdf  https://arxiv.org/pdf/2603.00078
curl -L -o 03-yapay-kisiler.pdf                   https://arxiv.org/pdf/2607.08695
curl -L -o 04-kimin-degerleri-cogulcu-uyum.pdf    https://arxiv.org/pdf/2604.20805
curl -L -o 05-agi-tanimi-savunma.pdf              https://arxiv.org/pdf/2510.18212
curl -L -o 06-agi-soylemi-elestirisi.pdf          https://arxiv.org/pdf/2401.13142
```

Ardından: `python main.py ingest --reset`
