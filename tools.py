import chromadb
from chromadb.utils import embedding_functions
import duckdb
import pandas as pd

# ChromaDB veritabanı yolu ve embedding modeli
DB_PATH = "./chroma_db"
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"

def get_chroma_collection():
    """ChromaDB koleksiyonuna bağlanır ve nesneyi döndürür."""
    embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL
    )
    client = chromadb.PersistentClient(path=DB_PATH)
    collection = client.get_collection(
        name="olist_reviews",
        embedding_function=embedding_func
    )
    return collection

def search_reviews(query: str, top_k: int = 3) -> str:
    """
    Kullanıcının sorusuna en uygun müşteri yorumlarını vektör veritabanından getirir.
    """
    try:
        collection = get_chroma_collection()
        
        # Kullanıcının sorusu vektöre çevrilip veritabanında aranıyor
        results = collection.query(
            query_texts=[query],
            n_results=top_k
        )
        
        # Sonuçları LLM'in okuyabileceği anlaşılır bir metin bloğuna çeviriyoruz
        documents = results['documents'][0]
        metadatas = results['metadatas'][0]
        
        response_text = "Bulunan İlgili Müşteri Yorumları:\n"
        for i in range(len(documents)):
            score = metadatas[i].get('score', 'Bilinmiyor')
            response_text += f"- (Memnuniyet Puanı: {score}/5): {documents[i]}\n"
            
        return response_text
    
    except Exception as e:
        return f"Yorum aranırken teknik bir hata oluştu: {str(e)}"

def execute_sql(sql_query: str) -> str:
    """
    Gelen SQL sorgusunu DuckDB üzerinde çalıştırır ve sonucu metin olarak döndürür.
    """
    try:
        # DuckDB'ye bellek içi bağlantı kuruyoruz.
        # Bu sayede ayrı bir veritabanı dosyasına ihtiyaç duymadan doğrudan CSV okuyabiliriz.
        con = duckdb.connect(database=':memory:')
        
        # SQL sorgusunu çalıştırıp sonucu bir Pandas DataFrame (tablo) olarak alıyoruz
        result_df = con.execute(sql_query).df()
        
        if result_df.empty:
            return "Sorgu başarıyla çalıştı ancak veri bulunamadı (Sonuç boş)."
        
        # DataFrame'i LLM'in anlayabileceği düz metin (string) formatına çeviriyoruz
        return result_df.to_string(index=False)
    
    except Exception as e:
        # Eğer LLM hatalı bir SQL yazarsa, sistemin çökmemesi için hatayı yakalayıp LLM'e iletiyoruz
        return f"SQL Çalıştırma Hatası: {str(e)}"

# Dosyayı doğrudan çalıştırdığımızda bu blok devreye girer
if __name__ == "__main__":
    print("--- 1. Vektör Arama (RAG) Testi ---")
    # "teslimat gecikti" anlamına gelen bir sorgu atıyoruz
    print(search_reviews("kargo çok geç geldi ve ürün hasarlıydı"))
    
    print("\n--- 2. SQL Çalıştırma Testi ---")
    # DuckDB'nin doğrudan klasördeki CSV'yi okuyabildiğini doğruluyoruz. 
    # Not: data klasöründe 'olist_orders_dataset.csv' olduğundan emin ol.
    test_query = """
    SELECT order_status, COUNT(*) as total_orders 
    FROM 'data/olist_orders_dataset.csv' 
    GROUP BY order_status 
    LIMIT 3
    """
    print(execute_sql(test_query))