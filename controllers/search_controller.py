from utils.preprocessing import preprocessing
from utils.weighting import calculate_tfidf_top_terms
from utils.similarity import calculate_similarity
from models.book import Book
from collections import defaultdict
from sqlalchemy.orm import joinedload
import numpy as np
import re
from functools import lru_cache

# Cache untuk preprocessing
@lru_cache(maxsize=1000)
def cached_preprocessing(text):
    return preprocessing(text)

def search_books_function(query):    
    # 1. Preprocessing query
    processed_query = set(cached_preprocessing(query))
    
    # 2. Query database
    books = (Book.query
             .options(
                 joinedload(Book.authors),
                 joinedload(Book.editors))
             .all())
    
    # 3. Preprocessing metadata
    processed_metadata_books = []
    book_mapping = {}  # Dictionary untuk mapping book_id ke index
    
    for idx, book in enumerate(books):
        # Menggunakan format key yang sama dengan yang dihasilkan calculate_tfidf_top_terms
        book_id = f'Buku {idx+1}'  # Sesuaikan dengan format yang diharapkan
        book_mapping[book_id] = idx
        
        authors = ' '.join(author.name for author in book.authors)
        editors = ' '.join(editor.name for editor in book.editors)
        
        processed_book = {
            "title": cached_preprocessing(book.title),
            "author": cached_preprocessing(authors),
            "editor": cached_preprocessing(editors),
            "publisher": cached_preprocessing(book.publisher),
            "description": cached_preprocessing(book.description),
        }
        processed_metadata_books.append(processed_book)
    
    # 4. Calculate TF-IDF
    top_terms = calculate_tfidf_top_terms(processed_metadata_books)
    
    # 5. Calculate similarities
    book_similarities = defaultdict(list)
    
    for book_id, tfidf_data in top_terms.items():
        terms = {item["term"] for item in tfidf_data}
        
        for query_term in processed_query:
            similarities = [
                calculate_similarity(query_term, term)
                for term in terms
            ]
            valid_similarities = [s for s in similarities if s is not None]
            if valid_similarities:
                book_similarities[book_id].extend(valid_similarities)
    
    # 6. Calculate statistics
    book_stats = []
    
    for book_id, similarities in book_similarities.items():
        if similarities:
            try:
                book_idx = book_mapping[book_id]
                book = books[book_idx]
                
                book_stats.append({
                    'id': book.id,
                    'title': book.title,
                    'average_similarity': np.mean(similarities),
                    'std_dev': np.std(similarities, ddof=0),
                    'cover': book.cover_link
                })
            except KeyError as e:
                print(f"Warning: Book ID {book_id} not found in mapping")
                continue
    
    # 7. Sort and return top 10
    return sorted(book_stats, key=lambda x: (-x['average_similarity'], x['std_dev']))[:10]