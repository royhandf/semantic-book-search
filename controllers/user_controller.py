from flask import request, flash, session
from werkzeug.security import check_password_hash
from flask_login import login_user  # Correct import from Flask-Login
from models.user import User

def signin_user_function():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Check if both fields are filled
        if not email or not password:
            flash('All fields must be filled!', 'danger')
            return None
        
        user = User.query.filter_by(email=email).first()
        
        # Verify if the user exists and the password matches
        if user and check_password_hash(user.password, password):
            login_user(user)  # Logs in the user
            session['user'] = {
                'name': user.name,
                'email': user.email,    
                'id': user.id
            }
            return user
        else:
            # Return None if authentication fails
            return None
