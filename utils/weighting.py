import math
import json
from extensions import redis_client
import hashlib
        
def compute_tf(term, document):
    return document.count(term) / len(document) if document else 0

def compute_idf(term, documents):
    df = sum(1 for document in documents if term in document)
    return math.log10(len(documents) / df) if df != 0 else 0

def compute_tfidf(tf, idf):
    return tf * idf
    
# Fungsi untuk menghitung TF-IDF dan mengambil N term teratas
def calculate_tfidf_top_terms(processed_metadata_books, scenario=3):
    metadata_key = hashlib.sha256(json.dumps(processed_metadata_books).encode('utf-8')).hexdigest()
    
    # Cek cache Redis
    cached_result = redis_client.get(metadata_key)
    if cached_result:
        # Jika ada cache, ambil data dan sesuaikan dengan scenario
        tfidf_books = json.loads(cached_result)
        result = {}
        # Ambil hanya scenario data dari 10 data teratas yang disimpan
        for book_id, terms in tfidf_books.items():
            result[book_id] = terms[:scenario]
        return result
    
    documents = [book["title"] + book["author"] + book["editor"] + book["publisher"] + book["description"]
                 for book in processed_metadata_books]

    all_terms = list(set(term for book in documents for term in book))
    idf_cache = {term: compute_idf(term, documents) for term in all_terms}
    
    tfidf_books = {}
    
    for i, book in enumerate(documents):
        tfidf_data = []
        
        for term in all_terms:
            tf_book = compute_tf(term, book)
            idf = idf_cache[term]
            tfidf_value = compute_tfidf(tf_book, idf)
            tfidf_data.append({
                "term": term,
                "tfidf": round(tfidf_value, 4)
            })

        # Ambil nilai TF-IDF tertinggi untuk setiap buku, simpan 10 data teratas
        top_terms = sorted(tfidf_data, key=lambda x: x["tfidf"], reverse=True)[:10]
        tfidf_books[f"Buku {i+1}"] = top_terms
    
    with redis_client.pipeline() as pipe:
        pipe.set(metadata_key, json.dumps(tfidf_books), ex=86400)  # Cache selama 1 hari
        pipe.execute()

    # Kembalikan hasil yang sesuai dengan scenario
    result = {}
    for book_id, terms in tfidf_books.items():
        result[book_id] = terms[:scenario]

    return result
