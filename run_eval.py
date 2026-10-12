import json
from agent import ask_ollama

def evaluate_routing():
    print("📊 Sistem Değerlendirmesi Başlıyor...\n")
    
    # Test verilerini güvenli bir şekilde okuyoruz
    try:
        with open('test_cases.json', 'r', encoding='utf-8') as f:
            tests = json.load(f)
    except FileNotFoundError:
        print("Hata: 'test_cases.json' dosyası bulunamadı. Lütfen proje dizininde olduğundan emin ol.")
        return

    basarili_yonlendirme = 0
    toplam_test = len(tests)

    for i, test in enumerate(tests, 1):
        soru = test["soru"]
        beklenen = test["beklenen_arac"]
        
        print(f"Test {i}/{toplam_test}")
        print(f"Soru: {soru}")
        
        # Sadece karar mekanizmasını (Routing) test eden özel istem
        routing_prompt = f"""
        Aşağıdaki kullanıcı sorusunu analiz et. 
        Eğer soru sipariş sayıları, kargo ücretleri, gelirler gibi sayısal hesaplama gerektiriyorsa SADECE "SQL" yaz.
        Eğer soru müşteri yorumları, şikayetler veya düşüncelerle ilgiliyse SADECE "RAG" yaz.
        Başka hiçbir açıklama yapma. Sadece SQL veya RAG kelimesini döndür.
        
        Kullanıcı Sorusu: {soru}
        Karar:
        """
        
        # LLM'den kararı alıyoruz ve metin temizliği yapıyoruz
        alinan_karar = ask_ollama(routing_prompt).strip().upper()
        
        # Modelin kararı ile JSON dosyamızdaki beklenen aracı karşılaştırıyoruz
        is_correct = beklenen in alinan_karar
        if is_correct:
            basarili_yonlendirme += 1
            print(f"✅ Başarılı: Beklenen '{beklenen}', Alınan '{alinan_karar}'")
        else:
            print(f"❌ Başarısız: Beklenen '{beklenen}', Alınan '{alinan_karar}'")
        print("-" * 40)

    # Nihai metrikleri hesaplıyoruz
    accuracy = (basarili_yonlendirme / toplam_test) * 100
    print(f"\n🎯 Genel Yönlendirme Başarısı (Routing Accuracy): %{accuracy:.1f}")
    print(f"Doğru Seçim: {basarili_yonlendirme}/{toplam_test}")

if __name__ == "__main__":
    evaluate_routing()