from sklearn.feature_extraction.text import TfidfVectorizer
import json
import hashlib
from extensions import redis_client

def calculate_tfidf_top_terms(processed_metadata_books, scenario=3, processed_query=None):
    metadata_key = hashlib.sha256(json.dumps(processed_metadata_books).encode('utf-8')).hexdigest()
    
    cached_result = redis_client.get(metadata_key)
    if cached_result:
        tfidf_books = json.loads(cached_result)
        result = {}
        for book_id, terms in tfidf_books.items():
            filtered_terms = filter_terms_by_query(terms, processed_query)[:scenario]
            result[book_id] = filtered_terms
        return result    
    
    # 1. Siapkan dokumen dari metadata buku
    documents = [
        " ".join(book["title"] + book["author"] + book["editor"] + book["publisher"] + book["description"])
        for book in processed_metadata_books
    ]

    # 2. Hitung TF-IDF dengan library sklearn tanpa preprocessing
    vectorizer = TfidfVectorizer(lowercase=False, tokenizer=None, preprocessor=None, stop_words=None)
    tfidf_matrix = vectorizer.fit_transform(documents)
    terms = vectorizer.get_feature_names_out()

    # 3. Ambil top-N terms berdasarkan bobot tertinggi untuk tiap buku
    tfidf_books = {}
    for i, row in enumerate(tfidf_matrix.toarray()):
        tfidf_data = [{"term": terms[idx], "tfidf": row[idx]} for idx in row.argsort()[-16:][::-1]] 
        filtered_terms = filter_terms_by_query(tfidf_data, processed_query)
        tfidf_books[f"Buku {i+1}"] = filtered_terms

    # 4. Simpan ke Redis
    serialized_data = json.dumps(tfidf_books)
    with redis_client.pipeline() as pipe:
        pipe.set(metadata_key, serialized_data, ex=86400)
        pipe.execute()

    # Kembalikan hasil yang sesuai dengan skenario
    result = {}
    for book_id, terms in tfidf_books.items():
        result[book_id] = terms[:scenario]
    return result

def filter_terms_by_query(terms, query_terms):
    return [
        term for term in terms
        if not any(query_term in term["term"] for query_term in (query_terms or []))
    ]
