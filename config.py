from dotenv import load_dotenv
from datetime import timedelta
import os

load_dotenv() 

class Config:
    DEBUG = os.getenv('DEBUG', True)
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI')
    SQLALCHEMY_TRACK_MODIFICATIONS = os.getenv('SQLALCHEMY_TRACK_MODIFICATIONS', False)
    SQLALCHEMY_POOL_SIZE = os.getenv('SQLALCHEMY_POOL_SIZE', 5)
    SQLALCHEMY_POOL_RECYCLE = os.getenv('SQLALCHEMY_POOL_RECYCLE', 3600)
    
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES')))
    
    SECRET_KEY = os.getenv('SECRET_KEY')
    UPLOAD_FOLDER_IMAGE = os.getenv('UPLOAD_FOLDER_IMAGE')
    UPLOAD_FOLDER_PDF = os.getenv('UPLOAD_FOLDER_PDF')
    ALLOWED_EXTENSIONS_IMAGE = set(os.getenv('ALLOWED_EXTENSIONS_IMAGE', 'png,jpg,jpeg').split(','))
    ALLOWED_EXTENSIONS_PDF = set(os.getenv('ALLOWED_EXTENSIONS_PDF', 'pdf').split(','))
    MAX_IMAGE_LENGTH = int(os.getenv('MAX_IMAGE_LENGTH', 2 * 1024 * 1024))  
    MAX_PDF_LENGTH = int(os.getenv('MAX_PDF_LENGTH', 50 * 1024 * 1024)) 
