from flask import request, current_app, jsonify
from extensions import db
from models.book import Book
from datetime import datetime
from urllib.parse import urlparse
import os

def is_full_url(url):
    return urlparse(url).scheme in ["http", "https"]

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def save_uploaded_file(file, folder_name, prefix, max_size, allowed_extensions):
    if file.filename == '':
        return None, jsonify({'error': 'No selected file'}), 400

    if not allowed_file(file.filename, allowed_extensions):
        return None, jsonify({'error': 'File type not allowed'}), 400

    if len(file.read()) > max_size:
        return None, jsonify({'error': f'File size too large. Max size is {max_size // (1024 * 1024)} MB'}), 400
    file.seek(0)

    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    extension = os.path.splitext(file.filename)[1]
    filename = f"{timestamp}_{prefix}{extension}"

    upload_folder = os.path.join(current_app.root_path, f'static/uploads/{folder_name}')
    os.makedirs(upload_folder, exist_ok=True)

    full_path = os.path.join(upload_folder, filename)
    file.save(full_path)

    return os.path.join('static/uploads', folder_name, filename).replace('\\', '/'), None, None

def add_book_function():
    if request.method != 'POST':
        return jsonify({'error': 'Invalid request method'}), 405

    form = request.form
    title = form.get('title')
    publisher = form.get('publisher')
    published = int(form.get('published')) if form.get('published', '').isdigit() else None
    isbn = form.get('isbn')
    description = form.get('description', '')
    table_of_contents = form.get('table_of_contents', '')
    authors = form.get('authors', '').strip()
    editors = form.get('editors', '').strip()

    pdf = request.files.get('pdf_link')
    image_cover = request.files.get('cover_link')

    if not pdf or not image_cover:
        return jsonify({'error': 'Both image and PDF are required'}), 400

    image_path, err, code = save_uploaded_file(
        image_cover, 'images', 'cover',
        current_app.config['MAX_IMAGE_LENGTH'],
        current_app.config['ALLOWED_EXTENSIONS_IMAGE']
    )
    if err:
        return err, code

    pdf_path, err, code = save_uploaded_file(
        pdf, 'pdfs', 'document',
        current_app.config['MAX_PDF_LENGTH'],
        current_app.config['ALLOWED_EXTENSIONS_PDF']
    )
    if err:
        return err, code

    book = Book(
        title=title,
        publisher=publisher,
        published=published,
        description=description,
        table_of_contents=table_of_contents,
        isbn=isbn,
        authors=authors,
        editors=editors,
        pdf_link=pdf_path,
        cover_link=image_path
    )

    book.save()

    return jsonify({
        "status": "success",
        "data": {
            **book.data,
            "language": "eng",
            "subject": "",
            "pdf_link": f"{request.host_url}{book.pdf_link}",
            "cover_link": f"{request.host_url}{book.cover_link}",
        }
    }), 201

def edit_book_function(book):
    if not book:
        return jsonify({'status': 'error', 'message': 'Book not found'}), 404

    form = request.form
    title = form.get('title')
    publisher = form.get('publisher')
    published = int(form.get('published')) if form.get('published', '').isdigit() else None
    isbn = form.get('isbn')
    description = form.get('description', '')
    table_of_contents = form.get('table_of_contents', '')
    authors = form.get('authors', '').strip()
    editors = form.get('editors', '').strip()

    if 'cover_link' in request.files:
        image_cover = request.files['cover_link']
        if image_cover.filename:
            if book.cover_link:
                old_path = os.path.join(current_app.root_path, book.cover_link)
                if os.path.exists(old_path):
                    os.remove(old_path)

            image_path, err, code = save_uploaded_file(
                image_cover, 'images', 'cover',
                current_app.config['MAX_IMAGE_LENGTH'],
                current_app.config['ALLOWED_EXTENSIONS_IMAGE']
            )
            if err:
                return err, code
            book.cover_link = image_path

    if 'pdf_link' in request.files:
        pdf = request.files['pdf_link']
        if pdf.filename:
            if book.pdf_link:
                old_path = os.path.join(current_app.root_path, book.pdf_link)
                if os.path.exists(old_path):
                    os.remove(old_path)

            pdf_path, err, code = save_uploaded_file(
                pdf, 'pdfs', 'document',
                current_app.config['MAX_PDF_LENGTH'],
                current_app.config['ALLOWED_EXTENSIONS_PDF']
            )
            if err:
                return err, code
            book.pdf_link = pdf_path

    book.title = title
    book.publisher = publisher
    book.published = published
    book.isbn = isbn
    book.description = description
    book.table_of_contents = table_of_contents
    book.authors = authors
    book.editors = editors

    db.session.commit()

    return jsonify({
        "status": "success",
        "data": {
            **book.data,
            "pdf_link": book.pdf_link if is_full_url(book.pdf_link) else f"{request.host_url}{book.pdf_link}",
            "cover_link": book.cover_link if is_full_url(book.cover_link) else f"{request.host_url}{book.cover_link}",
        }
    }), 200

def delete_book_function(book):
    try:
        for file_path in [book.pdf_link, book.cover_link]:
            if file_path:
                full_path = os.path.join(current_app.root_path, file_path)
                if os.path.exists(full_path):
                    os.remove(full_path)

        db.session.delete(book)
        db.session.commit()

        return jsonify({'status': 'success', 'message': 'Book successfully deleted'}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting book: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

def get_all_books(page=1, per_page=10, search=""):
    books_query = Book.query

    if search:
        like = f"%{search.lower()}%"
        books_query = books_query.filter(
            db.or_(
                db.func.lower(Book.title).like(like),
                db.func.lower(Book.publisher).like(like),
                db.func.lower(Book.authors).like(like),
                db.func.lower(Book.editors).like(like),
            )
        )

    paginated = books_query.order_by(Book.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)

    return {
        "results": [
            {
                **book.data,
                "pdf_link": book.pdf_link if is_full_url(book.pdf_link) else f"{request.host_url}{book.pdf_link}",
                "cover_link": book.cover_link if is_full_url(book.cover_link) else f"{request.host_url}{book.cover_link}",
            }
            for book in paginated.items
        ],
        "total_books": paginated.total,
        "total_pages": paginated.pages
    }