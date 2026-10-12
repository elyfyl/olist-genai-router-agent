# Olist E-Commerce: GenAI Data Analyst Agent

Bu proje, Brezilya merkezli Olist e-ticaret veri seti üzerinde çalışan, kullanıcının sorularını doğal dilde analiz edip doğru veri aracını seçen yerel bir LLM Router Agent uygulamasıdır. 

## 🎯 Proje Hedefi
Amacımız; kullanıcının sorusuna göre ya DuckDB üzerinden SQL sorgusu çalıştıran (sayısal veriler için) ya da ChromaDB üzerinden benzerlik araması yapan (müşteri yorumları için) akıllı bir Router geliştirmektir.

---

## 🚀 Adım Adım Geliştirme Süreci

Sistemi 4 ana mühendislik aşamasında geliştirdik:

### Adım 1: Veri Hazırlığı ve Vektör Veritabanı (RAG Katmanı)
İlk aşamada Olist müşteri yorumlarını okuyup, yapay zekanın anlayabileceği matematiksel vektörlere dönüştürdük ve bunları yerel bir veritabanına (**ChromaDB**) kaydettik. 
* **Multilingual Yaklaşım:** Brezilyalı müşterilerin Portekizce yorumlarını Türkçe veya İngilizce sorgulayabilmek için çok dilli bir model kullandık. Örneğin; Türkçe olarak *"kargo çok geç geldi ve ürün hasarlıydı"* diye aratmamıza rağmen, modelimiz Portekizce *"O produto veio estragado"* (Ürün bozuk geldi) yorumlarını başarıyla eşleştirerek semantik aramanın gücünü kanıtladı. Test süreçlerinin hızlı işlemesi adına bu aşama şimdilik ilk 1000 yorum ile sınırlandırılmıştır.

### Adım 2: Araçların Geliştirilmesi
Yapay zeka asistanımızın (Ollama LLM) dış dünyayla iletişim kurmasını sağlayacak iki temel Python fonksiyonunu `tools.py` içerisinde geliştirdik:
1. **`search_reviews(query, top_k=3)`:** Kullanıcının doğal dildeki sorusunu alır, ChromaDB veritabanında anlamsal arama yapar ve en yüksek eşleşme puanına sahip 3 müşteri yorumunu getirir.
2. **`execute_sql(sql_query)`:** LLM'in veri analizi için üreteceği SQL kodunu alır, **DuckDB** kullanarak doğrudan CSV veri setinde bellek içi (in-memory) çalıştırır ve matematiksel sonucu metin formatında döndürür.

### Adım 3: Router Agent Katmanı
Sistemin beyni olan routing mantığını kurguladık:
* Kullanıcı bir soru sorar.
* Soru önce Llama 3 modeline gider. Modele şu talimat verilmiştir: *"Eğer soru sayılar, toplamlar veya sipariş durumlarıyla ilgiliyse 'SQL' kararı ver. Eğer soru müşteri şikayetleri veya yorumlarla ilgiliyse 'RAG' kararı ver."*
* LLM'in verdiği karara göre Python kodumuz dinamik olarak doğru aracı çalıştırır.
* Elde edilen ham veriler tekrar LLM'e verilir ve kullanıcıya doğal dilde anlaşılır bir cevap sunulur.

### Adım 4: Değerlendirme ve JSON Mimarisi
 
* **Separation of Concerns:** Test sorularını Python kodunun içine gömmek yerine evrensel bir veri formatı olan **JSON** (`test_cases.json`) dosyasında tuttuk. Bu sayede ana test koduna (`run_eval.py`) hiç dokunmadan test setimizi güvenle genişletebiliriz.

---

## 🏗️ Sistem Mimarisi

Sistem, kullanıcının niyetine göre iki ana araç arasında dinamik routing yapar:
1. **Text-to-SQL (DuckDB):** Sayısal hesaplama, toplam hacim ve sipariş durumları gibi analitik soruları alıp bellek içi SQL sorgularına çevirerek doğrudan CSV üzerinden sonuç üretir.
2. **RAG (ChromaDB + Sentence Transformers):** Çok dilli embedding modeli kullanarak Portekizce metinler üzerinde semantik vektör araması yapar.

---

## 📊 Sistem Değerlendirmesi ve Başarı Oranı
Sistemin karar verme algoritmalarını ölçmek için özel JSON test seti üzerinden Routing Accuracy test edilmiştir.

* **Kullanılan Model:** Llama 3 (Ollama Local API)
* **Test Edilen Yetenek:** Kullanıcı niyetini anlama ve Doğru Aracı (SQL vs RAG) seçme kapasitesi
* **Ölçüm Metriği:** %100 Yönlendirme Başarısı (Routing Accuracy)

Ajan, sayısal analitik sorgular ile NLP tabanlı duygu analizi sorgularını hatasız bir şekilde ayrıştırarak halüsinasyon riskini minimize etmektedir.

```text
📊 Sistem Değerlendirmesi Başlıyor...

Test 1/4 - Soru: Sistemde toplam kaç adet iptal edilmiş sipariş var?
✅ Başarılı: Beklenen 'SQL', Alınan 'SQL'

Test 2/4 - Soru: Müşteriler ürünlerin paketlenmesi ve ambalaj kalitesi hakkında ne düşünüyor?
✅ Başarılı: Beklenen 'RAG', Alınan 'RAG'

Test 3/4 - Soru: Teslim edilen siparişlerin ortalama kargo ücreti nedir?
✅ Başarılı: Beklenen 'SQL', Alınan 'SQL'

Test 4/4 - Soru: Yanlış ürün gönderimiyle ilgili yapılan şikayetler nelerdir?
✅ Başarılı: Beklenen 'RAG', Alınan 'RAG'

🎯 Genel Yönlendirme Başarısı (Routing Accuracy): %100.0
Doğru Seçim: 4/4

```
--- 

## 💻 Örnek Çalışma Çıktıları

### Senaryo 1: Sayısal Analiz (Text-to-SQL)
> **Soru:** "Veritabanında toplam kaç tane teslim edilmiş sipariş var?"

> **Karar:** `🛠️ Seçilen Araç: SQL (Veritabanı Sorgusu)`

> **Yanıt:** "Total delivered orders in the database are 96,478."

### Senaryo 2: NLP Duygu Analizi (RAG)
> **Soru:** "Müşteriler kargo gecikmeleri hakkında neler söylüyor?"

> **Karar:** `🛠️ Seçilen Araç: RAG (Vektör Müşteri Yorumları Araması)`

> **Yanıt:** "Müşterileriniz kargo gecikmeleri konusunda şu anda şöyle konuşuyor: Bazıları kargo şirketinin hatalı olduğunu düşünüyor (Memnuniyet Puanı: 2.0/5)..."

---