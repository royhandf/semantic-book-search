from flask import Blueprint, render_template, jsonify, request
from models.book import Book
from models.user import User
from controllers.book_controller import get_all_books, add_book_function, edit_book_function, delete_book_function
from controllers.search_controller import search_books_function
from controllers.user_controller import signin_user_function, signup_user_function
from extensions import redis_client, db
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import IntegrityError
from urllib.parse import urlparse
import json

main = Blueprint('main', __name__)

@main.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@main.route('/api/signin', methods=['POST'])
def signin():
    return signin_user_function()

@main.route('/api/signup', methods=['POST'])
def signup():
    return signup_user_function()
    
@main.route('/logout')
def logout():
    return jsonify({
        "status": "success",
        "message": "You have been logged out."
    }), 200
    
@main.route('/api/books/search', methods=['GET'])
def search_books():
    query = request.args.get('query', '').strip()
    page = request.args.get('page', 1, type=int)
    
    if not query:
        return jsonify({
            "status": "error",
            "message": "Query parameter is required."
        }), 400

    try:
        all_results = search_books_function(query, page)
        
        cache_key = "related_books"
        redis_client.setex(cache_key, 3600, json.dumps(all_results['results'][:8]))
                
        return jsonify({
            "status": "success",
            "query": query,
            "total_results": all_results["total_results"],
            "total_pages": all_results["total_pages"],
            "current_page": all_results["current_page"],
            "data": all_results["results"]
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
    
@main.route('/api/books/<int:id>', methods=['GET'])
def book_detail(id):
    book = Book.get_by_id(id)
    if not book:
        return jsonify({"error": "Book not found"}), 404
    
    get_related_books_key = redis_client.get("related_books")

    related_books = []
    if get_related_books_key:
        related_books = json.loads(get_related_books_key)
        
    try:
        related_books = [b for b in related_books if b['id'] != id]
    
        return jsonify({
            "status": "success",
            "data": book.data,
            "related_books": related_books
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@main.route('/api/dashboard/books', methods=['GET'])
@jwt_required()
def books():
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=user_id).first()

    if user.role != 'admin':
        return jsonify({
            "status": "error",
            "message": "Unauthorized access"
        }), 403

    try:
        all_results = get_all_books()

        return jsonify({
            "status": "success",
            "data": all_results["results"]
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

        
@main.route('/api/dashboard/books/create', methods=['POST'])
@jwt_required()
def add_book():
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=user_id).first()

    if user.role != 'admin':
        return jsonify({
            "status": "error",
            "message": "Unauthorized access"
        }), 403

    try:
        return add_book_function()
        
    except IntegrityError as e: 
        db.session.rollback()  
        if '1062' in str(e.orig):
            return jsonify({
                "status": "error",
                "message": "A book with the same title already exists."
            }), 400 
        else:
            return jsonify({
                "status": "error",
                "message": "Database integrity error: " + str(e)
            }), 500  
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500  
    
@main.route('/api/dashboard/books/edit/<int:id>', methods=['GET', 'PUT'])
@jwt_required()
def edit_book(id):
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=user_id).first()

    if user.role != 'admin':
        return jsonify({
            "status": "error",
            "message": "Unauthorized access"
        }), 403

    try:  
        book = Book.get_by_id(id)
        
        def is_full_url(url):
            return urlparse(url).scheme in ["http", "https"]

        if request.method == 'GET':  
            return jsonify({
                "status": "success",
                "data": {
                    **book.data,
                    "pdf_link": book.pdf_link if is_full_url(book.pdf_link) else f"{request.host_url}{book.pdf_link}",
                    "cover_link": book.cover_link if is_full_url(book.cover_link) else f"{request.host_url}{book.cover_link}",
                }
            }), 200
        return edit_book_function(book)
    except IntegrityError as e:
        db.session.rollback()
        if '1062' in str(e.orig):
            return jsonify({
                "status": "error",
                "message": "A book with the same title already exists."
            }), 400
        else:
            return jsonify({
                "status": "error",
                "message": "Database integrity error: " + str(e)
            }), 500
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@main.route('/api/dashboard/books/delete/<int:id>', methods=['DELETE'])
def delete_book(id):
    try:
        book = Book.get_by_id(id)
        if not book:
            return jsonify({'status': 'error', 'message': 'Book not found'}), 404
        
        delete_book_function(book)
        return jsonify({'status': 'success', 'message': 'Book successfully deleted'}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500






