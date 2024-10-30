from flask import Flask
from config import Config
from extensions import db, login_manager
from flask_migrate import Migrate
from routes import main
from models.user import User

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    register_resources(app)
    register_extensions(app)

    return app

def register_extensions(app):
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'main.signin'  # Ensure this points to your sign-in route
    Migrate(app, db)

def register_resources(app):
    app.register_blueprint(main)
    
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

if __name__ == '__main__':
    app = create_app()
    app.run()
