from flask import request ,flash, session
from werkzeug.security import check_password_hash
from models.user import User
from extensions import db

def signup_user_function():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not name or not email or not password:
            flash('Semua field harus diisi!', 'danger')
            return None
        
        if User.query.filter_by(name=name).first():
            flash('Username sudah terdaftar!', 'danger')
            return None
        
        if User.query.filter_by(email=email).first():
            flash('Email sudah terdaftar!', 'danger')
            return None

        new_user = User(name=name, email=email)
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        return new_user
    
def signin_user_function():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Semua field harus diisi!', 'danger')
            return None
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            return user 
        else:
            raise ValueError("Invalid email or password.")
        
        