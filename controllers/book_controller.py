from flask import request, flash, current_app, url_for
from werkzeug.utils import secure_filename
from extensions import db
from models.book import Book
from models.author import Author
from models.editor import Editor
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
        pdf = request.files['pdf_link']
        image_cover = request.files['cover_link']
        
        if image_cover.filename == '':
            flash('No selected file')
            return None
        
        if pdf.filename == '':
            flash('No selected file')
            return None
        
        if not allowed_file_image(image_cover.filename):
            flash('File type not allowed')
            return None
        
        if not allowed_file_pdf(pdf.filename):
            flash('File type not allowed')
            return None
        
        image_filename = secure_filename(image_cover.filename)
        pdf_filename = secure_filename(pdf.filename)
        
        # Ensure the directory exists
        upload_folder_image = os.path.join(current_app.root_path, 'static/uploads/images')
        os.makedirs(upload_folder_image, exist_ok=True)
        
        upload_folder_pdf = os.path.join(current_app.root_path, 'static/uploads/pdfs')
        os.makedirs(upload_folder_pdf, exist_ok=True)

        image_full_path = os.path.join(upload_folder_image, image_filename)
        image_cover.save(image_full_path)
        
        pdf_full_path = os.path.join(upload_folder_pdf, pdf_filename)
        pdf.save(pdf_full_path)
        
        image_filepath = os.path.join('uploads', 'images', image_filename).replace('\\', '/')
        pdf_filepath = os.path.join('uploads', 'pdfs', pdf_filename).replace('\\', '/')
        
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
        
        book.save()
        
        author_names = request.form.get('authors', '').split(';')
        for name in author_names:
            name = name.strip()
            if name:
                author = Author(name=name, book_id=book.id)
                db.session.add(author)  # Tambahkan author ke session

        # Menyimpan editors
        editor_names = request.form.get('editors', '').split(';')
        for name in editor_names:
            name = name.strip()
            if name:
                editor = Editor(name=name, book_id=book.id)
                db.session.add(editor)  # Tambahkan editor ke session
            
        # Commit semua perubahan (authors dan editors)
        db.session.commit()

        # Data untuk response
        data = {
            'id': book.id,
            'title': book.title,
            'publisher': book.publisher,
            'published': book.published,
            'description': book.description,
            'isbn': book.isbn,
            'table_of_contents': book.table_of_contents,
            'pdf_link': book.pdf_link,
            'cover_link': book.cover_link,
            'authors': [author.name for author in book.authors],
            'editors': [editor.name for editor in book.editors]
        }

        return data
    
def is_external_link(url):
    parsed_url = urlparse(url)
    return parsed_url.netloc and parsed_url.netloc != '127.0.0.1'

def get_book_download_link(book):
    pdf_link = book.pdf_link
    if is_external_link(pdf_link):
        return pdf_link  # Link eksternal
    else:
        return url_for('static', filename=f'uploads/pdfs/{pdf_link.split("/")[-1]}')

def edit_book_function(book):
    if request.method == "POST":
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
    if book.pdf_link and os.path.exists(os.path.join(current_app.root_path, book.pdf_link)):
        os.remove(os.path.join(current_app.root_path, book.pdf_link))
    
    if book.cover_link and os.path.exists(os.path.join(current_app.root_path, book.cover_link)):
        os.remove(os.path.join(current_app.root_path, book.cover_link))
        
    db.session.delete(book)
    db.session.commit()

