from flask import Flask
from config import Config
from extensions import db
from flask_migrate import Migrate
from flask_cors import CORS 
from routes import main
from flask_jwt_extended import JWTManager

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app, supports_credentials=True) 
    register_resources(app)
    register_extensions(app)
    
    return app

def register_extensions(app):
    db.init_app(app)
    jwt = JWTManager(app)
    Migrate(app, db)

def register_resources(app):
    app.register_blueprint(main)

if __name__ == '__main__':
    app = create_app()
    app.run()
