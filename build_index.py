import pandas as pd
import chromadb
from chromadb.utils import embedding_functions
import os

def create_vector_db():
    # Veri seti ve veritabanı yolları tanımlanıyor
    csv_path = "data/olist_order_reviews_dataset.csv"
    db_path = "./chroma_db"
    
    if not os.path.exists(csv_path):
        print(f"Hata: '{csv_path}' bulunamadı. Lütfen CSV dosyasını 'data' klasörüne ekle.")
        return

    print("1. Veri seti yükleniyor...")
    df = pd.read_csv(csv_path)
    
    # Sadece metin içeren yorumları al ve hızlı test için ilk 1000 tanesini seç
    df = df.dropna(subset=['review_comment_message']).head(1000)
    print(f"Toplam {len(df)} yorum işlenecek.")

    print("2. Çok dilli (multilingual) embedding modeli başlatılıyor...")
    # Portekizce yorumları anlamlandırabilmesi için çok dilli model kullanıyoruz
    embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="paraphrase-multilingual-MiniLM-L12-v2"
    )
    
    client = chromadb.PersistentClient(path=db_path)
    
    # Eski koleksiyon varsa silip temiz bir başlangıç yapıyoruz
    try:
        client.delete_collection(name="olist_reviews")
    except Exception:
        pass
        
    collection = client.create_collection(
        name="olist_reviews", 
        embedding_function=embedding_func
    )

    print("3. Yorumlar vektör veritabanına kaydediliyor (Bu işlem birkaç dakika sürebilir)...")
    
    documents = df['review_comment_message'].astype(str).tolist()
    # Sonradan kaynak göstermek için ID ve Puanları meta veri olarak saklıyoruz
    metadatas = [{"review_id": str(row['review_id']), "score": float(row['review_score'])} for _, row in df.iterrows()]
    ids = [str(i) for i in range(len(df))]

    # Belleği yormamak için verileri 250'lik paketler halinde veritabanına yazıyoruz
    batch_size = 250
    for i in range(0, len(documents), batch_size):
        collection.add(
            documents=documents[i:i+batch_size],
            metadatas=metadatas[i:i+batch_size],
            ids=ids[i:i+batch_size]
        )
        print(f"İşlenen: {min(i+batch_size, len(documents))} / {len(documents)}")

    print("✅ Veritabanı oluşturuldu! Proje klasöründe 'chroma_db' dosyasını görebilirsin.")

if __name__ == "__main__":
    create_vector_db()