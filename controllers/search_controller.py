from utils.preprocessing import cached_preprocessing
from utils.weighting import calculate_tfidf_top_terms
from utils.similarity import calculate_similarity
from models.book import Book
from collections import defaultdict
import numpy as np
from math import ceil
from extensions import redis_client
from sqlalchemy import or_, text
import json

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

def search_books_function(query, scenario, page=1, per_page=12):    
    cache_key = f"search_results:{scenario}:{query.lower()}"
    cached_result = redis_client.get(cache_key)
    
    # delete cache redis key search_results:0:query
    redis_client.delete(f"search_results:-1:{query.lower()}")
    if cached_result:
        cached_data = json.loads(cached_result)
        if cached_data.get("query") == query and cached_data.get("scenario") == scenario:
            return paginate_books(cached_data["results"], page, per_page)        
            
    # 1. Preprocessing query
    processed_query = cached_preprocessing(query)

    # 4. Book database
    search_terms = query.lower().split()
    all_filters = []
    for term in search_terms:
        search_pattern = f'%{term}%'
        all_filters.append(Book.title.ilike(search_pattern))
        all_filters.append(Book.description.ilike(search_pattern))
    
    candidate_books = Book.query.filter(or_(*all_filters)).limit(2500).all()

    if not candidate_books:
        return paginate_books([], page, per_page)
        
    print(f"Ditemukan {len(candidate_books)} kandidat.")

    # 5. Preprocessing metadata
    metadata_cache_key = "processed_metadata_books"
    cached_metadata = redis_client.get(metadata_cache_key)
    if cached_metadata:        
        # 1. Dapatkan ID yang relevan dari hasil filter database. Ini "daftar belanja" kita.
        relevant_ids = {str(book.id) for book in candidate_books}

        # 2. Muat SELURUH metadata dari cache. Ganti nama variabel agar lebih jelas.
        all_metadata_from_cache = json.loads(cached_metadata)
        
        # 3. Saring/Filter metadata dari cache berdasarkan ID yang relevan. Ini langkah kuncinya.
        processed_metadata_books = [
            book_meta for book_meta in all_metadata_from_cache 
            if book_meta['id'] in relevant_ids
        ]
        
        # 4. Buat book_mapping dari candidate_books yang sudah difilter, bukan dari seluruh cache.
        book_mapping = {str(book.id): book for book in candidate_books}
    else:
        processed_metadata_books = []
        book_mapping = {}

        for book in candidate_books:
            book_id = str(book.id) 
            book_mapping[book_id] = book
            processed_metadata_books.append({
                "id": book_id,
                "title": cached_preprocessing(book.title),
                "author": cached_preprocessing(book.authors or ""),
                "editor": cached_preprocessing(book.editors or ""),
                "publisher": cached_preprocessing(book.publisher or ""),
                "description": cached_preprocessing(book.description or book.table_of_contents or ""),
            })
        print(f"Membuat cache metadata baru untuk kunci: {metadata_cache_key}")
        redis_client.set(metadata_cache_key, json.dumps(processed_metadata_books), ex=None) 
    
    # 6. Calculate similarities
    book_similarities = defaultdict(list)
    
    if scenario == 0:
        for book in processed_metadata_books:
            all_terms  = set(
                book.get('title', []) + book.get('description', [])
            )
            for query in processed_query:
                similarities = [calculate_similarity(query, term) for term in all_terms]
                if similarities:
                    book_similarities[book["id"]].extend(similarities)

    elif scenario == 3 or scenario == 5 or scenario == 10:
        # 7. Calculate TF-IDF
        top_terms = calculate_tfidf_top_terms(processed_metadata_books, scenario, processed_query)
        
        processed_metadata_map = {book['id']: book for book in processed_metadata_books}

        # 8. Calculate similarities for top terms
        for book_id, tfidf_data in top_terms.items():
            book = book_mapping.get(book_id)
            if not book:
                continue
            
            current_book_metadata = processed_metadata_map.get(book_id)
            if current_book_metadata:
                all_book_terms_set = set(
                    current_book_metadata.get('title', []) +
                    # current_book_metadata.get('author', []) +
                    # current_book_metadata.get('editor', []) +
                    # current_book_metadata.get('publisher', []) +
                    current_book_metadata.get('description', [])
                )
                                     
            for query in processed_query:
                if query in all_book_terms_set:
                    book_similarities[book_id].append(1.0)
                    
                for item in tfidf_data:
                    term = item["term"]
                    similarity = calculate_similarity(query, term)
                    book_similarities[book_id].append(similarity)
                    
    elif scenario == -1:
        for book in processed_metadata_books:
             # get all terms from book metadata
            all_book_terms_set = set(
                book.get('title', []) +
                book.get('author', []) +
                book.get('editor', []) +
                book.get('publisher', []) 
            )

            query_words_set = set(processed_query)
            found_words = query_words_set.intersection(all_book_terms_set)
            
            # Hitung skor presisi sesuai rumus Anda: (kata cocok / total kata query)
            matched_word_count = len(found_words)
            total_query_word_count = len(query_words_set)
            
            score = matched_word_count / total_query_word_count if total_query_word_count > 0 else 0.0

            book_similarities[book["id"]] = [score]
            
    # 9. Calculate statistics
    book_stats = []
    for book_id, similarities in book_similarities.items():
        if similarities:
            try:
                book = book_mapping[book_id]

                avg_similarity = np.mean(similarities)

                if avg_similarity >= 0.25: 
                    if scenario == -1:
                        title_lowercase = book.title.lower()
                        query_lowercase = query.lower()
                        title_contains_query = query_lowercase in title_lowercase
                        
                        book_stats.append({
                            'id': book.id,
                            'title': book.title,
                            'average_similarity': avg_similarity,
                            'similarity_count': len(similarities),
                            'std_dev': np.std(similarities, ddof=0),
                            'cover': book.cover_link,
                            'title_contains_query': title_contains_query 
                        })
                    else:
                        # Untuk skenario lain, gunakan format seperti biasa
                        book_stats.append({
                            'id': book.id,
                            'title': book.title,
                            'average_similarity': avg_similarity,
                            'similarity_count': len(similarities),
                            'std_dev': np.std(similarities, ddof=0),
                            'cover': book.cover_link
                        })
            except KeyError:
                continue
          
    # 10. Sort and cache results
    if scenario == -1:
        book_lists = sorted(book_stats, key=lambda x: (
            -int(x.get('title_contains_query', False)),  
            -x['average_similarity'],                   
        ))
        
        for book in book_lists:
            if 'title_contains_query' in book:
                del book['title_contains_query']
    else:
        book_lists = sorted(book_stats, key=lambda x: (-x['average_similarity'], x['std_dev']))
    redis_client.set(cache_key, json.dumps({"query": query, "scenario": scenario, "results": book_lists}), ex=3600) 

    return paginate_books(book_lists, page, per_page)