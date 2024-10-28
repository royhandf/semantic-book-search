from flask import Blueprint, render_template, redirect, url_for, jsonify, flash, request
from models.book import Book
from controllers.book_controller import add_book_function, get_book_download_link, edit_book_function, delete_book_function
from controllers.search_controller import search_books_function
from controllers.user_controller import signup_user_function, signin_user_function

main = Blueprint('main', __name__)

@main.route('/', methods=['GET'])
def index():
    return render_template('index.html')

# register admin
@main.route('/signup', methods=['GET', 'POST'])
def signup():
    try:
        signup_user_function()
        flash("User successfully registered!", "success")
    except Exception as e:
        flash(f"An error occurred while registering the user: {str(e)}", "error")
    
    return redirect(url_for('main.index'))

@main.route('/signin', methods=['GET', 'POST'])
def signin():
    try:
        signin_user_function()
        flash("You are now signed in!", "success")
    except Exception as e:
        flash("Sign in failed. Please check your email and password.", "error")
    return redirect(url_for('main.index'))

@main.route('/search', methods=['GET'])
def search():
    query = request.args.get('query') 
    if query:
        results = search_books_function(query)
        return render_template('search_results.html', results=results, query=query)
    else:
        flash("Please enter a search query.", "warning")
        return redirect(url_for('main.index'))

@main.route('/book/<int:id>', methods=['GET'])
def book_detail(id):
    book = Book.get_by_id(id)
    if book:
        return render_template('book_detail.html', book=book)

# dashboard/books
@main.route('/dashboard/books', methods=['GET'])
def books():
    books = Book.get_all()
    return render_template('books.html', books=books)

# dashboard/book create
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
        return redirect(pdf_link)  # Redirect ke link download
    return jsonify({'error': 'Book not found'}), 404

@main.route('/dashboard/book/<int:id>/details', methods=['GET'])
def get_description_contents(id):
    data = Book.get_description_contents_by_id(id)
    if data:
        return jsonify(data)
    return jsonify({'error': 'Book not found'}), 404