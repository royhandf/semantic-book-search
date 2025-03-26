from flask import request, current_app, jsonify
from extensions import db
from models.book import Book
from models.author import Author
from models.editor import Editor
from models.category import Category
from models.book_category import book_category
from datetime import datetime
from urllib.parse import urlparse
import os

def add_book_function():
    if request.method == 'POST':
        title = request.form.get('title')
        publisher = request.form.get('publisher')
        published = request.form.get('published')
        
        if published and published.isdigit(): 
            published = int(published)  
        else:
            published = None  
            
        isbn = request.form.get('isbn')
        description = request.form.get('description', '')
        table_of_contents = request.form.get('table_of_contents', '')
        category_ids = request.form.getlist('categories')
        pdf = request.files['pdf_link']
        image_cover = request.files['cover_link']
        
        if image_cover.filename == '' or pdf.filename == '':    
            return jsonify({'error': 'No selected file'}), 400
        
        if not allowed_file_image(image_cover.filename) or not allowed_file_pdf(pdf.filename):
            return jsonify({'error': 'File type not allowed'}), 400
        
        if len(image_cover.read()) > current_app.config['MAX_IMAGE_LENGTH']:
            return jsonify({'error': 'File size too large. Max size is 2 MB'}), 400
        
        if len(pdf.read()) > current_app.config['MAX_PDF_LENGTH']:
            return jsonify({'error': 'File size too large. Max size is 50 MB'}), 400
        
        image_cover.seek(0)
        pdf.seek(0)
        
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        
         # Mendapatkan ekstensi dari nama file asli
        image_extension = os.path.splitext(image_cover.filename)[1]
        pdf_extension = os.path.splitext(pdf.filename)[1]

        # Menentukan nama file dengan timestamp dan ekstensi file
        image_filename = f"{timestamp}_cover{image_extension}"
        pdf_filename = f"{timestamp}_document{pdf_extension}"
        
        upload_folder_image = os.path.join(current_app.root_path, 'static/uploads/images')
        os.makedirs(upload_folder_image, exist_ok=True)
        
        upload_folder_pdf = os.path.join(current_app.root_path, 'static/uploads/pdfs')
        os.makedirs(upload_folder_pdf, exist_ok=True)

        image_full_path = os.path.join(upload_folder_image, image_filename)
        image_cover.save(image_full_path)
        
        pdf_full_path = os.path.join(upload_folder_pdf, pdf_filename)
        pdf.save(pdf_full_path)
        
        image_filepath = os.path.join('static/uploads', 'images', image_filename).replace('\\', '/')
        pdf_filepath = os.path.join('static/uploads', 'pdfs', pdf_filename).replace('\\', '/')
        
        book = Book(
            title=title,
            publisher=publisher,
            published=published,
            description=description,
            isbn=isbn,
            table_of_contents=table_of_contents,
            pdf_link=pdf_filepath,
            cover_link=image_filepath
        )
        
        db.session.add(book)
        db.session.commit()             
        
        categories = Category.query.filter(Category.id.in_(category_ids)).all()
        book.categories.extend(categories)

        author_names = request.form.get('authors', '').split(';')
        for name in author_names:
            name = name.strip()
            if name:
                author = Author(name=name, book_id=book.id)
                db.session.add(author) 

        editor_names = request.form.get('editors', '').split(';')
        for name in editor_names:
            name = name.strip()
            if name:
                editor = Editor(name=name, book_id=book.id)
                db.session.add(editor)
            
        db.session.commit()

        return jsonify({
            "status": "success",
            "data": {
                'id': book.id,
                'title': book.title,
                'publisher': book.publisher,
                'published': book.published,
                'description': book.description,
                'isbn': book.isbn,
                'table_of_contents': book.table_of_contents,    
                "pdf_link": f"{request.host_url}{book.pdf_link}",
                "cover_link": f"{request.host_url}{book.cover_link}",
                'authors': [author.name for author in book.authors],
                'editors': [editor.name for editor in book.editors],
                'categories': [category.id for category in book.categories]
            }
        }), 201
        
def edit_book_function(book):
    if not book:
        return jsonify({'status': 'error', 'message': 'Book not found'}), 404
    
    if request.method == 'PUT':
        title = request.form.get('title')
        publisher = request.form.get('publisher')
        published = request.form.get('published')
        
        if published and published.isdigit():
            published = int(published)
        else:
            published = None
            
        isbn = request.form.get('isbn')
        description = request.form.get('description', '')
        table_of_contents = request.form.get('table_of_contents', '')
        category_ids = request.form.getlist('categories')
        
        # Handle file uploads if new files are provided
        if 'cover_link' in request.files:
            image_cover = request.files['cover_link']
            if image_cover.filename != '':
                if not allowed_file_image(image_cover.filename):
                    return jsonify({'error': 'Image file type not allowed'}), 400
                if len(image_cover.read()) > current_app.config['MAX_IMAGE_LENGTH']:
                    return jsonify({'error': 'Image file size too large. Max size is 2 MB'}), 400
                image_cover.seek(0)
                
                # Delete old image if it exists
                old_cover_path = os.path.join(current_app.root_path, book.cover_link)
                if book.cover_link and os.path.exists(old_cover_path):
                    os.remove(old_cover_path)
                
                # Save new image
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                image_extension = os.path.splitext(image_cover.filename)[1]
                image_filename = f"{timestamp}_cover{image_extension}"
                upload_folder_image = os.path.join(current_app.root_path, 'static/uploads/images')
                os.makedirs(upload_folder_image, exist_ok=True)
                image_full_path = os.path.join(upload_folder_image, image_filename)
                image_cover.save(image_full_path)
                book.cover_link = os.path.join('static/uploads', 'images', image_filename).replace('\\', '/')
        
        if 'pdf_link' in request.files:
            pdf = request.files['pdf_link']
            if pdf.filename != '':
                if not allowed_file_pdf(pdf.filename):
                    return jsonify({'error': 'PDF file type not allowed'}), 400
                if len(pdf.read()) > current_app.config['MAX_PDF_LENGTH']:
                    return jsonify({'error': 'PDF file size too large. Max size is 50 MB'}), 400
                pdf.seek(0)
                
                # Delete old PDF if it exists
                old_pdf_path = os.path.join(current_app.root_path, book.pdf_link)
                if book.pdf_link and os.path.exists(old_pdf_path):
                    os.remove(old_pdf_path)
                
                # Save new PDF
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                pdf_extension = os.path.splitext(pdf.filename)[1]
                pdf_filename = f"{timestamp}_document{pdf_extension}"
                upload_folder_pdf = os.path.join(current_app.root_path, 'static/uploads/pdfs')
                os.makedirs(upload_folder_pdf, exist_ok=True)
                pdf_full_path = os.path.join(upload_folder_pdf, pdf_filename)
                pdf.save(pdf_full_path)
                book.pdf_link = os.path.join('static/uploads', 'pdfs', pdf_filename).replace('\\', '/')

        # 📝 Update book data
        book.title = title
        book.publisher = publisher
        book.published = published
        book.description = description
        book.isbn = isbn
        book.table_of_contents = table_of_contents

        if category_ids:
            categories = Category.query.filter(Category.id.in_(category_ids)).all()
            book.categories = categories
        else:
            book.categories = []

        # Update authors
        Author.query.filter_by(book_id=book.id).delete()
        author_names = request.form.get('authors', '').split(';')
        for name in author_names:
            name = name.strip()
            if name:
                author = Author(name=name, book_id=book.id)
                db.session.add(author)
        
        # Update editors
        Editor.query.filter_by(book_id=book.id).delete()
        editor_names = request.form.get('editors', '').split(';')
        for name in editor_names:
            name = name.strip()
            if name:
                editor = Editor(name=name, book_id=book.id)
                db.session.add(editor)
        
        db.session.commit()
        
        def is_full_url(url):
            return urlparse(url).scheme in ["http", "https"]
        
        return jsonify({
            "status": "success",
            "data": {
                'id': book.id,
                'title': book.title,
                'publisher': book.publisher,
                'published': book.published,
                'description': book.description,
                'isbn': book.isbn,
                'table_of_contents': book.table_of_contents,
                "pdf_link": book.pdf_link if is_full_url(book.pdf_link) else f"{request.host_url}{book.pdf_link}",
                "cover_link": book.cover_link if is_full_url(book.cover_link) else f"{request.host_url}{book.cover_link}",
                'authors': [author.name for author in book.authors],
                'editors': [editor.name for editor in book.editors],
                'categories': [category.id for category in book.categories]
            }
        }), 200

def delete_book_function(book):
    try:
        # Hapus referensi dari tabel books_categories terlebih dahulu
        db.session.execute(book_category.delete().where(book_category.c.book_id == book.id))
        db.session.commit()
        current_app.logger.info(f"References in books_categories for book {book.id} deleted.")

        # Hapus file PDF dan cover jika ada
        pdf_path = os.path.join(current_app.root_path, book.pdf_link)
        cover_path = os.path.join(current_app.root_path, book.cover_link)

        if book.pdf_link and os.path.exists(pdf_path):
            os.remove(pdf_path)
        
        if book.cover_link and os.path.exists(cover_path):
            os.remove(cover_path)

        # Hapus buku dari database
        db.session.delete(book)
        db.session.commit()
        current_app.logger.info(f"Book {book.id} successfully deleted.")

        return jsonify({'status': 'success', 'message': 'Book successfully deleted'}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting book: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

def is_full_url(url):
    return urlparse(url).scheme in ["http", "https"]

def get_all_books(page=1, per_page=10, search=""):
    books_query = Book.query.options(db.joinedload(Book.categories))

    if search:
        search_filter = f"%{search.lower()}%"
        books_query = books_query.filter(
            db.or_(
                db.func.lower(Book.title).like(search_filter)
            )
        )
        
    books_query = books_query.order_by(Book.created_at.desc())

    paginated_books = books_query.paginate(page=page, per_page=per_page, error_out=False)

    return {
        'results': [
            {
                **book.data,
                "pdf_link": book.pdf_link if is_full_url(book.pdf_link) else f"{request.host_url}{book.pdf_link}",
                "cover_link": book.cover_link if is_full_url(book.cover_link) else f"{request.host_url}{book.cover_link}",
                "categories": [category.name for category in book.categories] 
            }
            for book in paginated_books.items
        ],
        "total_books": paginated_books.total,
        "total_pages": paginated_books.pages
    }
    
def allowed_file_image(filename):
    allowed_extensions = current_app.config['ALLOWED_EXTENSIONS_IMAGE']
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def allowed_file_pdf(filename):
    allowed_extensions = current_app.config['ALLOWED_EXTENSIONS_PDF']
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions