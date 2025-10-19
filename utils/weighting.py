from sklearn.feature_extraction.text import TfidfVectorizer
import json
from extensions import redis_client

def calculate_tfidf_top_terms(processed_metadata_books, scenario=3, processed_query=None):
    metadata_key = "tfidf_all_books"
    
    cached_result = redis_client.get(metadata_key)
    if cached_result:
        tfidf_books = json.loads(cached_result)
        valid_book_ids = [book["id"] for book in processed_metadata_books]
        return {
            book_id: terms[:scenario] 
            for book_id, terms in tfidf_books.items()
            if book_id in valid_book_ids
        }
    
    # 1. dokumen dari metadata buku
    documents = [
        " ".join(book["title"] + book["description"])
        for book in processed_metadata_books
    ]

    # 2. Hitung TF-IDF dengan library sklearn tanpa preprocessing
    vectorizer = TfidfVectorizer(lowercase=False, tokenizer=None, preprocessor=None, stop_words=None)
    tfidf_matrix = vectorizer.fit_transform(documents)
    terms = vectorizer.get_feature_names_out()

    # 3. Ambil top-N terms berdasarkan bobot tertinggi untuk tiap buku
    tfidf_books = {}
    for i, row in enumerate(tfidf_matrix.toarray()):
        tfidf_data = [{"term": terms[idx], "tfidf": row[idx]} for idx in row.argsort()[-10:][::-1]] 
        book_id = processed_metadata_books[i]["id"]
        tfidf_books[book_id] = tfidf_data

    # 4. Simpan ke Redis
    serialized_data = json.dumps(tfidf_books)
    with redis_client.pipeline() as pipe:
        pipe.set(metadata_key, serialized_data, ex=None)
        pipe.execute()
        
    with open(f"tfidf_results.json", "w", encoding="utf-8") as f:
        json.dump(tfidf_books, f, indent=4, ensure_ascii=False)
        
    # Kembalikan hasil yang sesuai dengan skenario
    result = {}
    for book_id, terms in tfidf_books.items():
        result[book_id] = terms[:scenario]  

    return result

