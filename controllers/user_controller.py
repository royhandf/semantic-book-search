from flask import request, jsonify
from models.user import User
from flask_jwt_extended import create_access_token
from datetime import timedelta
from extensions import db

def signin_user_function():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    
    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400
    
    user = User.query.filter_by(email=email).first()
    
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid email or password"}), 401
    
    access_token = create_access_token(identity=str(user.id), expires_delta=timedelta(days=1))
        
    username = user.name.replace(" ", "+")
    
    return jsonify({
        "status": "success",
        "token": access_token,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "avatar": f'https://ui-avatars.com/api/?name={username}&size=128&background=random',
            "role": user.role
        }
    }), 200
    
def signup_user_function():
    data = request.get_json()
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    
    # validasi input
    if not name or not email or not password:
        return jsonify({"error": "Name, email, and password are required"}), 400
    
    # cek email sudah terdaftar atau belum
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 400
    
    new_user = User(name=name, email=email, role="user")
    new_user.set_password(password)
    
    try:
        db.session.add(new_user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to register user"}), 500
    
    # Langsung login setelah berhasil registrasi
    access_token = create_access_token(identity=str(new_user.id), expires_delta=timedelta(days=1))
    username = new_user.name.replace(" ", "+")
    
    return jsonify({
        "status": "success",
        "token": access_token,
        "user": {
            "id": new_user.id,
            "name": new_user.name,
            "email": new_user.email,
            "avatar": f'https://ui-avatars.com/api/?name={username}&size=128&background=random',
            "role": new_user.role
        }
    }), 201
    
def get_all_users_function():
    try:
        all_users = User.get_all()
        return jsonify({
            "status": "success",
            "data": [user.data for user in all_users]
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
        
def edit_user_function(user, data):
    try:
        user.name = data.get("name", user.name)
        user.email = data.get("email", user.email)
        
        if 'password' in data and data['password'].strip():
            user.set_password(data['password'])
            
        db.session.commit()
        
        return {
            "message": "User successfully updated",
            "data": user.data
        }
    except Exception as e:
        db.session.rollback()
        return { "message": str(e) }

def delete_user_function(user):
    try:
        db.session.delete(user)
        db.session.commit()
        return { "message": "User successfully deleted" }
    except Exception as e:
        db.session.rollback()
        return { "message": str(e) }
