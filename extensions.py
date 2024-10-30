from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import spacy
import nltk

# download resources
nltk.download('stopwords')
nltk.download('wordnet')

db = SQLAlchemy()
login_manager = LoginManager()

nlp = spacy.load('en_core_web_sm')