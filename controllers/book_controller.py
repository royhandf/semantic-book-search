from flask import request, current_app, jsonify
from werkzeug.utils import secure_filename
from extensions import db
from models.book import Book
from models.author import Author
from models.editor import Editor
from math import ceil
from datetime import datetime
from urllib.parse import urlparse
import os

def allowed_file_image(filename):
    allowed_extensions = current_app.config['ALLOWED_EXTENSIONS_IMAGE']
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def allowed_file_pdf(filename):
    allowed_extensions = current_app.config['ALLOWED_EXTENSIONS_PDF']
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

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
        
        image_filename = f"{timestamp}_{secure_filename(image_cover.filename)}"
        pdf_filename = f"{timestamp}_{secure_filename(pdf.filename)}"
        
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
                'editors': [editor.name for editor in book.editors]
            }
        }), 201
        
def edit_book_function(book):
    if request.method == 'POST':
        title = request.form['title']
        publisher = request.form['publisher']
        published = request.form.get('published')
        
        if published and published.isdigit(): 
            published = int(published)  
        else:
            published = None  
            
        isbn = request.form['isbn']
        description = request.form.get('description', '')
        table_of_contents = request.form.get('table_of_contents', '')        

        # Mengupdate atribut buku
        book.title = title
        book.publisher = publisher
        book.published = published
        book.description = description
        book.isbn = isbn
        book.table_of_contents = table_of_contents

        # Menghapus penulis dan editor lama dari database
        db.session.query(Author).filter(Author.book_id == book.id).delete()
        db.session.query(Editor).filter(Editor.book_id == book.id).delete()

        # Menyimpan penulis baru
        author_names = request.form.get('authors', '').split(';')
        for name in author_names:
            name = name.strip()
            if name:
                author = Author(name=name, book_id=book.id)
                db.session.add(author)  # Tambahkan author ke session

        # Menyimpan editors baru
        editor_names = request.form.get('editors', '').split(';')
        for name in editor_names:
            name = name.strip()
            if name:
                editor = Editor(name=name, book_id=book.id)
                db.session.add(editor)  # Tambahkan editor ke session
            
        # Cek dan hapus file cover lama jika ada file baru yang diunggah
        if 'cover_link' in request.files and request.files['cover_link'].filename != '':
            image_cover = request.files['cover_link']
            if allowed_file_image(image_cover.filename):
                # Hapus cover lama
                if book.cover_link:
                    old_cover_path = os.path.join(current_app.root_path, book.cover_link)
                    if os.path.exists(old_cover_path):
                        os.remove(old_cover_path)
                
                # Simpan cover baru
                image_filename = secure_filename(image_cover.filename)
                upload_folder_image = os.path.join(current_app.root_path, 'static/uploads/images')
                os.makedirs(upload_folder_image, exist_ok=True)
                image_full_path = os.path.join(upload_folder_image, image_filename)
                image_cover.save(image_full_path)
                book.cover_link = os.path.join('uploads', 'images', image_filename).replace('\\', '/')

        # Cek dan hapus file PDF lama jika ada file baru yang diunggah
        if 'pdf_link' in request.files and request.files['pdf_link'].filename != '':
            pdf = request.files['pdf_link']
            if allowed_file_pdf(pdf.filename):
                # Hapus PDF lama
                if book.pdf_link:
                    old_pdf_path = os.path.join(current_app.root_path, book.pdf_link)
                    if os.path.exists(old_pdf_path):
                        os.remove(old_pdf_path)
                
                # Simpan PDF baru
                pdf_filename = secure_filename(pdf.filename)
                upload_folder_pdf = os.path.join(current_app.root_path, 'static/uploads/pdfs')
                os.makedirs(upload_folder_pdf, exist_ok=True)
                pdf_full_path = os.path.join(upload_folder_pdf, pdf_filename)
                pdf.save(pdf_full_path)
                book.pdf_link = os.path.join('uploads', 'pdfs', pdf_filename).replace('\\', '/')

        # Simpan ke database
        db.session.commit()
                
        print(image_full_path)
        data = {
            'id': book.id,
            'title': book.title,
            'publisher': book.publisher,
            'published': book.published,
            'description': book.description,
            'isbn': book.isbn,
            'table_of_contents': book.table_of_contents,
            'cover_link': book.cover_link,
            'pdf_link': book.pdf_link,
            'authors': [author.name for author in book.authors],
            'editors': [editor.name for editor in book.editors]
        }
        
        return data

def delete_book_function(book):
    pdf_path = os.path.join(current_app.root_path, book.pdf_link)
    cover_path = os.path.join(current_app.root_path, book.cover_link)

    if book.pdf_link and os.path.exists(pdf_path):
        try:
            os.remove(pdf_path)
        except Exception as e:
            return jsonify({'status': 'error','message': f"Error deleting PDF file: {e}"}), 500
    else:
        return jsonify({'status': 'error','message': 'PDF not found or invalid path'}), 404

    if book.cover_link and os.path.exists(cover_path):
        try:
            os.remove(cover_path)
        except Exception as e:
            return jsonify({'status': 'error','message': f"Error deleting cover file: {e}"}), 500
    else:
        return jsonify({'status': 'error','message': 'Cover not found or invalid path'}), 404

    db.session.delete(book)
    db.session.commit()

def get_all_books(page=1, per_page=5):
    books = Book.query.order_by(Book.created_at.desc()).all()   

    total_results = len(books)
    total_pages = ceil(total_results / per_page)
    
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_results = books[start_idx:end_idx]
    
    def is_full_url(url):
        return urlparse(url).scheme in ["http", "https"]
    
    return {
        'total_results': total_results,
        'total_pages': total_pages,
        'current_page': page,
        'results': [
            {
                **book.data,
                "pdf_link": book.pdf_link if is_full_url(book.pdf_link) else f"{request.host_url}{book.pdf_link}",
                "cover_link": book.cover_link if is_full_url(book.cover_link) else f"{request.host_url}{book.cover_link}",
            }
            for book in paginated_results
        ]
    }