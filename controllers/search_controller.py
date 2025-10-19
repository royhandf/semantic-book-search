from utils.preprocessing import cached_preprocessing
from utils.weighting import calculate_tfidf_top_terms
from utils.similarity import calculate_similarity
from models.book import Book
from collections import defaultdict
import numpy as np
from math import ceil
from extensions import redis_client
from sqlalchemy import or_
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

    redis_client.delete(f"search_results:-1:{query.lower()}")
    if cached_result:
        cached_data = json.loads(cached_result)
        if cached_data.get("query") == query and cached_data.get("scenario") == scenario:
            return paginate_books(cached_data["results"], page, per_page)   
            
    processed_query = cached_preprocessing(query)

    search_terms = query.lower().split()
    filters = []
    for term in search_terms:
        like_pattern = f"%{term}%"
        filters.append(Book.title.ilike(like_pattern))
        filters.append(Book.description.ilike(like_pattern))

    candidate_books = Book.query.filter(or_(*filters)).limit(2500).all()
    if not candidate_books:
        return paginate_books([], page, per_page)
        
    metadata_cache_key = "processed_metadata_books"
    cached_metadata = redis_client.get(metadata_cache_key)
    if cached_metadata:
        relevant_ids = {str(book.id) for book in candidate_books}
        all_cached = json.loads(cached_metadata)
        processed_metadata_books = [
            meta for meta in all_cached if meta["id"] in relevant_ids
        ]
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
        redis_client.set(metadata_cache_key, json.dumps(processed_metadata_books), ex=None)

    book_similarities = defaultdict(list)
    
    if scenario == 0:
        for book in processed_metadata_books:
            all_terms = set(book.get("title", []) + book.get("description", []))
            for q in processed_query:
                similarities = [calculate_similarity(q, term) for term in all_terms]
                if similarities:
                    book_similarities[book["id"]].extend(similarities)
    elif scenario in (3, 5, 10):
        top_terms = calculate_tfidf_top_terms(processed_metadata_books, scenario)
        meta_map = {book["id"]: book for book in processed_metadata_books}

        for book_id, tfidf_data in top_terms.items():
            book = book_mapping.get(book_id)
            if not book:
                continue
            current_meta = meta_map.get(book_id)
            if current_meta:
                all_terms = set(
                    current_meta.get("title", []) +
                    current_meta.get("description", [])
                )
            for q in processed_query:
                if q in all_terms:
                    book_similarities[book_id].append(1.0)
                for item in tfidf_data:
                    term = item["term"]
                    similarity = calculate_similarity(q, term)
                    book_similarities[book_id].append(similarity)
    elif scenario == -1:
        for book in processed_metadata_books:
            all_terms = set(
                book.get("title", []) +
                book.get("author", []) +
                book.get("editor", []) +
                book.get("publisher", [])
            )
            query_words = set(processed_query)
            found_words = query_words.intersection(all_terms)
            matched = len(found_words)
            total_query = len(query_words)
            score = matched / total_query if total_query > 0 else 0.0
            book_similarities[book["id"]] = [score]
            
    book_stats = []
    for book_id, similarities in book_similarities.items():
        if not similarities:
            continue
        try:
            book = book_mapping[book_id]
            avg_similarity = np.mean(similarities)
            if avg_similarity >= 0.4:
                data = {
                    "id": book.id,
                    "title": book.title,
                    "average_similarity": avg_similarity,
                    "similarity_count": len(similarities),
                    "std_dev": np.std(similarities, ddof=0),
                    "cover": book.cover_link,
                }
                if scenario == -1:
                    title_contains = query.lower() in book.title.lower()
                    data["title_contains_query"] = title_contains
                book_stats.append(data)
        except KeyError:
            continue

    if scenario == -1:
        book_lists = sorted(
            book_stats,
            key=lambda x: (
                -int(x.get("title_contains_query", False)),
                -x["average_similarity"],
            ),
        )
        for book in book_lists:
            book.pop("title_contains_query", None)
    else:
        book_lists = sorted(book_stats, key=lambda x: (-x["average_similarity"], x["std_dev"]))

    redis_client.set(
        cache_key,
        json.dumps({"query": query, "scenario": scenario, "results": book_lists}),
        ex=3600,
    )

    return paginate_books(book_lists, page, per_page)