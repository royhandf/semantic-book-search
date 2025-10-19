import json
import mysql.connector

def import_json_to_mysql(filename):
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='semantic_book_search'
    )
    cursor = conn.cursor()

    with open(filename, 'r', encoding='utf-8') as file:
        data = json.load(file)

    publications = data.get('publications', [])
    print(f"Jumlah publikasi: {len(publications)}")

    for pub in publications:
        m = pub.get('metadata', {})
        if not m:
            continue

        language_list = m.get('language') or []
        if 'eng' not in language_list:
            continue

        title = m.get('title') or ''
        authors = ', '.join(m.get('author', [])) if m.get('author') else ''
        editors = ', '.join(m.get('editor', [])) if m.get('editor') else ''  # Tambahan editor
        description = m.get('description') or ''
        publisher = m.get('publisher') or ''
        published = m.get('published') or 0
        subject = ', '.join(m.get('subject', [])) if m.get('subject') else ''
        isbn = ', '.join(m.get('isbn', [])) if m.get('isbn') else ''
        pdf_link = pub.get('links', {}).get('href') or ''
        cover_link = pub.get('images', {}).get('href') or ''

        sql = '''
            INSERT INTO books (
                title, authors, editors, language, description, publisher,
                published, subject,
                isbn, pdf_link, cover_link
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        '''
        values = (
            title, authors, editors, ', '.join(language_list), description, publisher,
            published, subject,
            isbn, pdf_link, cover_link
        )

        try:
            cursor.execute(sql, values)
        except Exception as e:
            print(f"Gagal menyimpan data buku: {title} | Error: {e}")
            continue

    conn.commit()
    cursor.close()
    conn.close()
    print("Import selesai.")

# Jalankan fungsi
import_json_to_mysql('OAPENLibrary.json')
