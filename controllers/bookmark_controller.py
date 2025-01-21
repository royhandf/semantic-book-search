from flask import request, jsonify
from extensions import db
from models import User, Book, Bookmark

def add_bookmark_function():
    data = request.get_json()
    user_id = data.get('user_id')
    book_id = data.get('book_id')
    
    if not user_id or not book_id:
        return jsonify({
            "status": "error",
            "message": "User ID and Book ID are required."
        }), 400
        
    user = User.get_by_id(user_id)
    book = Book.get_by_id(book_id)
    if not user or not book:
        return jsonify({
            "status": "error",
            "message": "User or Book not found."
        }), 404
        
    existing_bookmark = Bookmark.query.filter_by(user_id=user_id, book_id=book_id).first()
    if existing_bookmark:
        return jsonify({
            "status": "error",
            "message": "Bookmark already exists."
        }), 400
        
    bookmark = Bookmark(user_id=user_id, book_id=book_id)
    db.session.add(bookmark)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': 'Bookmark added successfully.',
        'data': bookmark.data
    }), 201
    
def get_user_bookmarks_function(user_id):
    bookmarks = Bookmark.get_by_user_id(user_id)
    
    if not bookmarks:
        return jsonify({
            'status': 'error',
            'message': 'No bookmarks found.'
        }), 404
    return jsonify({
        'status': 'success',
        'data': bookmarks
    }), 200
    
def delete_bookmark_function(id):
    bookmark = Bookmark.get_by_id(id)

    if not bookmark:
        return jsonify({'status': 'error', 'message': 'Bookmark not found'}), 404
    
    db.session.delete(bookmark)
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Bookmark successfully deleted'}), 200

