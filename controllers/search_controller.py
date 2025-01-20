from utils.preprocessing import cached_preprocessing
from utils.weighting import calculate_tfidf_top_terms
from utils.similarity import calculate_similarity
from models.book import Book
from collections import defaultdict
import numpy as np
from math import ceil
from sqlalchemy.orm import joinedload
from extensions import redis_client
import json

def search_books_function(query, scenario, page=1, per_page=12):    
    cache_key = "search_results"
    cached_result = redis_client.get(cache_key)
        
    if cached_result:
        cached_data = json.loads(cached_result)
        if cached_data.get("query") == query and cached_data.get("scenario") == scenario:
            return paginate_books(cached_data["results"], page, per_page)        
            
    # 1. Preprocessing query
    processed_query = cached_preprocessing(query)
    
    # 2. Book database
    books = Book.query.options(joinedload(Book.authors), joinedload(Book.editors)).all()
    
    # 3. Preprocessing metadata
    processed_metadata_books = []
    book_mapping = {} 
    
    for idx, book in enumerate(books):
        book_id = f'Buku {idx+1}'
        book_mapping[book_id] = idx
                
        processed_book = {
            "title": cached_preprocessing(book.title),
            "author": cached_preprocessing(' '.join(author.name for author in book.authors)),
            "editor": cached_preprocessing(' '.join(editor.name for editor in book.editors)),
            "publisher": cached_preprocessing(book.publisher),
            "description": cached_preprocessing(book.description if book.description else book.table_of_contents),
        }
        processed_metadata_books.append(processed_book)
        
    # 5. Calculate similarities
    book_similarities = defaultdict(list)
    
    if scenario == 0:
         for idx, book in enumerate(processed_metadata_books, start=1):
            all_terms = book["title"] + book["author"] + book["editor"] + book["publisher"] + book["description"]
            for query in processed_query:
                similarities = [
                    calculate_similarity(query, term)
                    for term in all_terms
                ]
                if similarities:
                    book_similarities[f'Buku {idx}'].extend(similarities)
    else:
        # 4. Calculate TF-IDF
        top_terms = calculate_tfidf_top_terms(processed_metadata_books, scenario)
        # 5. Calculate similarities
        for book_id, tfidf_data in top_terms.items():
            terms = {item["term"] for item in tfidf_data}
            for query_term in processed_query:
                similarities = [
                    calculate_similarity(query_term, term)
                    for term in terms
                ]
                if similarities:
                    book_similarities[book_id].extend(similarities)
                                        
    # 6. Calculate statistics
    book_stats = []
    
    for book_id, similarities in book_similarities.items():
        if similarities:
            try:
                book_idx = book_mapping[book_id]
                book = books[book_idx]

                avg_similarity = np.mean(similarities)
                if avg_similarity >= 0.5: 
                    book_stats.append({
                        'id': book.id,
                        'title': book.title,
                        'average_similarity': avg_similarity,
                        'std_dev': np.std(similarities, ddof=0),
                        'cover': book.cover_link
                    })
            except KeyError:
                continue

    book_lists = sorted(book_stats, key=lambda x: (-x['average_similarity'], x['std_dev']))  # Sort high to low
    redis_client.set(cache_key, json.dumps({"query": query, "scenario": scenario, "results": book_lists}), ex=86400) 
    return paginate_books(book_lists, page, per_page)

def paginate_books(books, page, per_page):
    total_results = len(books)
    total_pages = ceil(total_results / per_page)
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_results = books[start_idx:end_idx]

    return {
        "total_results": total_results,
        "total_pages": total_pages,
        "current_page": page,
        "results": paginated_results,
    }