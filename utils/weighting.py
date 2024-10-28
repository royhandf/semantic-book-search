import math
        
def compute_tf(term, document):
    return document.count(term) / len(document) if document else 0

def compute_idf(term, documents):
    df = sum(1 for document in documents if term in document)
    return math.log10(len(documents) / df) if df != 0 else 0

def compute_tfidf(tf, idf):
    return tf * idf
    
# Fungsi untuk menghitung TF-IDF dan mengambil N term teratas
def calculate_tfidf_top_terms(processed_metadata_books, top_n=3):
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
                # "tf": round(tf_book, 4),
                # "idf": round(idf, 4),
                "tfidf": round(tfidf_value, 4)
            })

        # Ambil nilai TF-IDF tertinggi untuk setiap buku
        top_terms = sorted(tfidf_data, key=lambda x: x["tfidf"], reverse=True)[:top_n]
        tfidf_books[f"Buku {i+1}"] = top_terms

    return tfidf_books
