from utils.preprocessing import cached_preprocessing
from utils.weighting import calculate_tfidf_top_terms
from utils.similarity import calculate_similarity
from models.book import Book
from collections import defaultdict
import numpy as np
from math import ceil
from extensions import redis_client
from sqlalchemy import or_, text, func # Tambahkan 'func' untuk MySQL FTS
import json
from extensions import db
import time

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
    overall_start = time.time()
    cache_key = f"search_results:{scenario}:{query.lower()}"
    cached_result = redis_client.get(cache_key)

    # Preprocessing query
    start = time.time()
    processed_query = cached_preprocessing(query)
    print(f"[⏱] Preprocessing query selesai dalam {time.time() - start:.3f} detik.")

    # Ambil kandidat buku dari DB menggunakan FTS
    start = time.time()
    candidate_books = []
    relevance_scores_map = {} # Untuk menyimpan skor relevansi setiap buku
    try:
        # FTS Query untuk mendapatkan ID dan relevance_score
        fts_ranked_query = text(f"""
            SELECT
                books.id,
                MATCH (books.title, books.description, books.authors, books.editors) AGAINST (:fts_query IN NATURAL LANGUAGE MODE) AS relevance_score
            FROM books
            WHERE MATCH (books.title, books.description, books.authors, books.editors)
                AGAINST (:fts_query IN NATURAL LANGUAGE MODE) > 0.0 # Hanya ambil yang memiliki skor > 0
            ORDER BY relevance_score DESC
            LIMIT :limit_count
        """)
        raw_results = db.session.execute(fts_ranked_query, {
            'fts_query': query,
            'limit_count': 2000 # Ambil sejumlah kandidat yang relevan
        }).fetchall()

        # Ekstrak ID buku dan skor relevansinya
        relevant_book_ids_ordered = [row.id for row in raw_results]
        relevance_scores_map = {row.id: row.relevance_score for row in raw_results}

        # Ambil objek buku lengkap berdasarkan ID yang sudah diurutkan dan difilter oleh FTS
        if relevant_book_ids_ordered:
            # Mengambil objek buku dari DB berdasarkan ID
            # Penting: Saat mengambil buku dengan Book.query.filter(Book.id.in_()),
            # hasilnya tidak akan terurut sesuai relevance_score secara default.
            # Jadi kita perlu mengurutkannya secara manual setelah diambil.
            candidate_books_unsorted = Book.query.filter(Book.id.in_(relevant_book_ids_ordered)).all()
            
            # Urutkan kembali candidate_books berdasarkan relevance_score dari FTS
            # Kita perlu membuat mapping dari ID ke objek buku untuk pengurutan
            book_id_to_obj_map = {book.id: book for book in candidate_books_unsorted}
            candidate_books = [book_id_to_obj_map[book_id] for book_id in relevant_book_ids_ordered if book_id in book_id_to_obj_map]
        else:
            candidate_books = []

    except Exception as e:
        print(f"[⚠] Gagal FTS: {e}, fallback ke LIKE")
        search_terms = query.lower().split()
        all_filters = []
        for term in search_terms:
            search_pattern = f'%{term}%'
            all_filters.append(Book.title.ilike(search_pattern))
            all_filters.append(Book.description.ilike(search_pattern))
            all_filters.append(Book.authors.ilike(search_pattern)) # Tambahkan juga authors dan editors
            all_filters.append(Book.editors.ilike(search_pattern))
        
        # Untuk fallback LIKE, kita tidak punya relevance_score dari database,
        # jadi kita akan mengurutkan secara kasar atau membiarkannya saja.
        # Jika Anda ingin FTS lebih kuat, pastikan indeks FTS terkonfigurasi dengan benar.
        candidate_books = Book.query.filter(or_(*all_filters)).limit(5000).all()
        # Dalam kasus fallback LIKE, tidak ada skor relevansi dari DB.
        # Jika ingin menyimulasikan skor, Anda bisa menghitung jumlah kecocokan di sini,
        # tapi itu tidak akan seakurat FTS.

    print(f"[⏱] Ambil kandidat dari DB selesai dalam {time.time() - start:.3f} detik.")

    if not candidate_books:
        print("[🚫] Tidak ditemukan kandidat buku.")
        return paginate_books([], page, per_page)

    print(f"Ditemukan {len(candidate_books)} kandidat.") # Log jumlah kandidat

    # Preprocessing metadata (dari Redis atau hitung manual)
    start = time.time()
    metadata_cache_key = "processed_metadata_books"
    cached_metadata = redis_client.get(metadata_cache_key)
    processed_metadata_books = []
    book_mapping = {}
    
    # Ambil hanya metadata untuk buku-buku yang merupakan kandidat
    candidate_book_ids_set = {str(book.id) for book in candidate_books}

    if cached_metadata:
        all_metadata_from_cache = json.loads(cached_metadata)
        # Filter metadata yang relevan dengan kandidat buku saat ini
        processed_metadata_books = [b for b in all_metadata_from_cache if b['id'] in candidate_book_ids_set]
        # Buat mapping untuk semua kandidat buku
        book_mapping = {str(book.id): book for book in candidate_books}
    else:
        # Jika tidak ada cache, proses semua metadata buku yang ada di DB
        # Kemudian simpan ke cache dan gunakan untuk kandidat buku saat ini
        all_books_from_db = Book.query.all() # Ambil semua buku untuk preprocessing metadata
        all_processed_metadata = []
        for book in all_books_from_db:
            book_id = str(book.id)
            all_processed_metadata.append({
                "id": book_id,
                "title": cached_preprocessing(book.title),
                "author": cached_preprocessing(book.authors or ""),
                "editor": cached_preprocessing(book.editors or ""),
                "publisher": cached_preprocessing(book.publisher or ""),
                "description": cached_preprocessing(book.description or book.table_of_contents or ""),
            })
            # Buat mapping untuk semua kandidat buku
            if book.id in candidate_book_ids_set:
                book_mapping[book_id] = book
        
        redis_client.set(metadata_cache_key, json.dumps(all_processed_metadata), ex=None)
        
        # Sekarang filter `processed_metadata_books` hanya untuk kandidat yang ditemukan
        processed_metadata_books = [b for b in all_processed_metadata if b['id'] in candidate_book_ids_set]

    print(f"[⏱] Preprocessing metadata selesai dalam {time.time() - start:.3f} detik.")

    # Hitung kemiripan
    start = time.time()
    book_similarities = defaultdict(list)

    if scenario == 0:
        for book_meta in processed_metadata_books: # Gunakan book_meta karena sudah diproses
            all_terms = set(book_meta.get('title', []) + book_meta.get('description', []))
            for q in processed_query:
                sims = [calculate_similarity(q, t) for t in all_terms]
                book_similarities[book_meta["id"]].extend(sims)

    elif scenario in {3, 5, 10}:
        # Pastikan calculate_tfidf_top_terms menerima list of dict seperti processed_metadata_books
        top_terms = calculate_tfidf_top_terms(processed_metadata_books, scenario, processed_query)
        processed_metadata_map = {b['id']: b for b in processed_metadata_books}
        for book_id, tfidf_data in top_terms.items():
            book = book_mapping.get(int(book_id)) # Pastikan ID sesuai tipe
            if not book: continue
            meta = processed_metadata_map.get(book_id)
            if meta:
                all_terms = set(meta.get('title', []) + meta.get('description', []))
                for q in processed_query:
                    if q in all_terms:
                        book_similarities[book_id].append(1.0)
                    for item in tfidf_data:
                        sim = calculate_similarity(q, item["term"])
                        book_similarities[book_id].append(sim)

    elif scenario == -1:
        for book_meta in processed_metadata_books: # Gunakan book_meta
            all_terms = set(book_meta.get('title', []) + book_meta.get('author', []) +
                            book_meta.get('editor', []) + book_meta.get('publisher', []))
            qset = set(processed_query)
            matched = qset.intersection(all_terms)
            score = len(matched) / len(qset) if qset else 0.0
            book_similarities[book_meta["id"]] = [score]

    print(f"[⏱] Perhitungan kemiripan selesai dalam {time.time() - start:.3f} detik.")

    # Statistik + sorting
    start = time.time()
    book_stats = []
    for book_id, sims in book_similarities.items():
        if sims:
            book = book_mapping.get(int(book_id)) # Pastikan ID sesuai tipe
            if not book: continue # Pastikan buku ditemukan di mapping
            avg = np.mean(sims)
            
            # Gabungkan skor FTS dengan skor kemiripan yang dihitung aplikasi
            # Ini adalah bagian di mana Anda "memfilter sesuai relevansi score" dari DB
            # dan mengkombinasikannya dengan perhitungan aplikasi.
            # Anda bisa memberikan bobot lebih pada FTS_score jika dianggap lebih penting.
            
            # Dapatkan FTS score, jika ada (hanya tersedia jika FTS berhasil)
            fts_score = relevance_scores_map.get(book.id, 0.0)
            
            # Contoh sederhana penggabungan: rata-rata berbobot
            # Sesuaikan bobotnya sesuai preferensi Anda.
            # Misalnya, 70% dari FTS score, 30% dari average_similarity
            combined_score = (fts_score * 0.70) + (avg * 0.30)
            
            # Anda bisa menyesuaikan ambang batas ini setelah menggabungkan skor
            if combined_score >= 0.15: # Ambang batas untuk menampilkan hasil
                stat = {
                    'id': book.id,
                    'title': book.title,
                    'average_similarity': round(avg * 100, 2),
                    'fts_relevance_score': round(fts_score, 4), # Tampilkan skor FTS juga
                    'combined_score': round(combined_score * 100, 2), # Tampilkan skor gabungan
                    'similarity_count': len(sims),
                    'std_dev': round(np.std(sims, ddof=0) * 100, 2),
                    'cover': book.cover_link
                }
                if scenario == -1:
                    stat['title_contains_query'] = query.lower() in book.title.lower()
                book_stats.append(stat)

    if scenario == -1:
        # Untuk skenario -1, tetap urutkan berdasarkan logika spesifiknya
        book_stats.sort(key=lambda x: (-int(x.get('title_contains_query', False)), -x['average_similarity']))
        for book in book_stats:
            book.pop('title_contains_query', None)
    else:
        # Untuk skenario lain, urutkan berdasarkan 'combined_score' yang baru
        book_stats.sort(key=lambda x: (-x['combined_score'], x['std_dev']))
    print(f"[⏱] Sorting & akhir selesai dalam {time.time() - start:.3f} detik.")

    print(f"[✅] Total waktu eksekusi: {time.time() - overall_start:.3f} detik.")
    return paginate_books(book_stats, page, per_page)