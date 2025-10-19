from sklearn.feature_extraction.text import TfidfVectorizer
import json
from extensions import redis_client

def calculate_tfidf_top_terms(processed_metadata_books, scenario=3):
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
    
    documents = [
        " ".join(book["title"] + book["description"])
        for book in processed_metadata_books
    ]

    vectorizer = TfidfVectorizer(lowercase=False, tokenizer=None, preprocessor=None, stop_words=None)
    tfidf_matrix = vectorizer.fit_transform(documents)
    terms = vectorizer.get_feature_names_out()

    tfidf_books = {}
    for i, row in enumerate(tfidf_matrix.toarray()):
        tfidf_data = [
            {"term": terms[idx], "tfidf": row[idx]}
            for idx in row.argsort()[-10:][::-1]
        ]
        book_id = processed_metadata_books[i]["id"]
        tfidf_books[book_id] = tfidf_data

    serialized_data = json.dumps(tfidf_books)
    with redis_client.pipeline() as pipe:
        pipe.set(metadata_key, serialized_data, ex=None)
        pipe.execute()
        
    return {book_id: terms[:scenario] for book_id, terms in tfidf_books.items()}
