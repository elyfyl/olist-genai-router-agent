import requests
import json
from tools import search_reviews, execute_sql

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3" 

def ask_ollama(prompt, system_prompt="Sen profesyonel ve net cevaplar veren kıdemli bir veri analistisin. Hayal ürünü bilgiler uydurma, sadece elindeki veriye odaklan."):
    """Ollama API'sine istek atar ve metin cevabını döndürür."""
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "system": system_prompt,
        "stream": False
    }
    
    try:
        response = requests.post(OLLAMA_URL, json=payload)
        response.raise_for_status()
        return response.json().get("response", "").strip()
    except requests.exceptions.RequestException as e:
        return f"Ollama bağlantı hatası: {e}. Ollama'nın çalıştığından emin olun."

def router_agent(user_question):
    """Soruyu analiz edip SQL veya RAG araçlarından hangisinin kullanılacağına karar verir."""
    
    print(f"\nSoru: '{user_question}'")
    print("🤖 Düşünüyorum (Hangi aracı kullanmalıyım?)...")
    
    # 1. Aşama: Karar Verme (Routing)
    routing_prompt = f"""
    Aşağıdaki kullanıcı sorusunu analiz et. 
    Eğer soru sipariş sayıları, durumları, kargo sayımları, gelirler gibi sayısal hesaplama gerektiriyorsa SADECE "SQL" yaz.
    Eğer soru müşteri yorumları, şikayetler veya insanların düşünceleri ile ilgiliyse SADECE "RAG" yaz.
    Başka hiçbir açıklama yapma.
    
    Kullanıcı Sorusu: {user_question}
    Karar (SQL veya RAG):
    """
    
    decision = ask_ollama(routing_prompt).upper()
    
    # 2. Aşama: Aracı Çalıştırma ve Cevap Üretme
    if "SQL" in decision:
        print("🛠️ Seçilen Araç: SQL (Veritabanı Sorgusu)")
        
        # LLM'i daha katı sınırlarla yönlendiriyoruz
        sql_generation_prompt = f"""
        Sen bir SQL uzmanısın. Aşağıdaki soruyu cevaplamak için SADECE geçerli bir DuckDB SQL sorgusu yaz.
        Tablo adı tam olarak tırnak içinde şudur: 'data/olist_orders_dataset.csv'
        Sütunlar: order_id, customer_id, order_status, order_purchase_timestamp
        
        DİKKAT: Hiçbir açıklama yapma. Markdown (```sql veya ```) KULLANMA. Sadece SELECT ile başlayan kodu yaz.
        
        Soru: '{user_question}'
        """
        sql_query = ask_ollama(sql_generation_prompt)
        
        # Python ile güvenlik katmanı: LLM markdown koyarsa temizliyoruz
        sql_query_clean = sql_query.replace("```sql", "").replace("```", "").strip()
        print(f"📝 Çalıştırılacak Temiz SQL: {sql_query_clean}")
        
        # Aracı çalıştır
        tool_result = execute_sql(sql_query_clean)
        
    elif "RAG" in decision:
        print("🛠️ Seçilen Araç: RAG (Vektör Müşteri Yorumları Araması)")
        # Aracı çalıştır
        tool_result = search_reviews(user_question, top_k=3)
        
    else:
        return "Sorunun türü anlaşılamadı."

    # 3. Aşama: Sonuçları yorumlayıp kullanıcıya sunma
    print("🧠 Araçlardan veri geldi, nihai cevap hazırlanıyor...")
    final_prompt = f"""
    Kullanıcının sorusu: {user_question}
    Veritabanından/Araçtan gelen gerçek veri: 
    {tool_result}
    
    Görev: Bu gerçek veriyi kullanarak kullanıcıya net ve kısa bir Türkçe cevap yaz. 
    Veride görünmeyen hiçbir bilgiyi uydurma. Sadece veriyi özetle.
    """
    
    final_answer = ask_ollama(final_prompt)
    return final_answer

if __name__ == "__main__":
    # Test 1: Sayısal veritabanı sorusu (SQL tetiklenmeli)
    cevap_1 = router_agent("Veritabanında toplam kaç tane teslim edilmiş (delivered) sipariş var?")
    print(f"\nYanıt: {cevap_1}\n")
    print("-" * 50)
    
    # Test 2: Yorum/Metin sorusu (RAG tetiklenmeli)
    cevap_2 = router_agent("Müşteriler kargo gecikmeleri hakkında neler söylüyor?")
    print(f"\nYanıt: {cevap_2}\n")