from flask import Blueprint, render_template, redirect, url_for, jsonify, flash, request, session
from models.book import Book
from math import ceil
from controllers.book_controller import add_book_function, get_book_download_link, edit_book_function, delete_book_function
from controllers.search_controller import search_books_function
from controllers.user_controller import signin_user_function
from flask_login import login_required

main = Blueprint('main', __name__)

@main.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@main.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        user = signin_user_function()
        
        if user:
            flash("You are now signed in!", "success")
            return redirect(url_for('main.books')) 
        
        flash("Sign in failed. Please check your email and password.", "error")
        return redirect(url_for('main.index')) 
    
    return render_template('index.html') 
    
@main.route('/logout')
def logout():
    session.pop('user', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))

@main.route('/books/search', methods=['GET'])
async def search():
    sort_option = request.args.get('sort', 'high_to_low')
    query = request.args.get('query', '')
    page = request.args.get('page', 1, type=int)
    per_page = 12
    
    if not query:
        flash("Please enter a search query.", "error")
        return redirect(request.referrer or url_for('main.index'))
    
    all_results = await search_books_function(query, sort_option)
    
    session['search_histories'] = [book for book in all_results[:10]]
    
    total_results = len(all_results)
    total_pages = ceil(total_results / per_page)

    # Calculate start and end page for pagination
    start_page = max(1, page - 2)
    end_page = min(total_pages, page + 2)

    page_range = list(range(start_page, end_page + 1))

    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_results = all_results[start_idx:end_idx]

    return render_template(
        'search_results.html',
        results=paginated_results,
        query=query,
        current_page=page,
        total_pages=total_pages,
        total_results=total_results,
        page_range=page_range,
        sort_option=sort_option,
        start_page=start_page, 
        end_page=end_page       
    )

    
@main.route('/books/<int:id>', methods=['GET'])
def book_detail(id):
    book = Book.get_by_id(id)
    if not book:
        flash("Book not found", "error")
        return redirect(url_for('main.index'))

    # Ambil hasil pencarian dari sesi
    related_books = session.get('search_histories', [])
    # Hapus buku yang sedang dilihat dari daftar rekomendasi
    related_books = [b for b in related_books if b['id'] != id]

    return render_template('book_detail.html', book=book, related_books=related_books)

# dashboard/books
@main.route('/dashboard/books', methods=['GET'])
@login_required
async def books():
    books = await Book.get_all() 
    user = session.get('user') 
    return render_template('books.html', books=books, user=user)

@main.route('/dashboard/book/create', methods=['POST'])
def add_book():
    try:
        add_book_function()  
        flash("Book successfully added!", "success")
    except Exception as e:
        flash(f"An error occurred while adding the book: {str(e)}", "error")
    
    return redirect(url_for('main.books'))
    
@main.route('/dashboard/book/edit/<int:id>', methods=['POST'])
def edit_book(id):
    try:  
        book = Book.get_by_id(id)
        edit_book_function(book) 
        flash("Book successfully updated!", "success")
    except Exception as e:
        flash(f"An error occurred while editing the book: {str(e)}", "error")
    return redirect(url_for('main.books'))

@main.route('/dashboard/book/delete/<int:id>', methods=['POST'])
def delete_book(id):
    try:
        book = Book.get_by_id(id)
        delete_book_function(book)
        flash("Book successfully deleted!", "success")
    except Exception as e:
        flash(f"An error occurred while deleting the book: {str(e)}", "error")
    return redirect(url_for('main.books'))

@main.route('/dashboard/book/<int:book_id>/download', methods=['GET'])
def download_pdf(book_id):
    book = Book.get_by_id(book_id)
    if book:
        pdf_link = get_book_download_link(book)
        return redirect(pdf_link) 
    return jsonify({'error': 'Book not found'}), 404

@main.route('/dashboard/book/<int:id>/details', methods=['GET'])
def get_description_contents(id):
    data = Book.get_description_contents_by_id(id)
    if data:
        return jsonify(data)
    return jsonify({'error': 'Book not found'}), 404