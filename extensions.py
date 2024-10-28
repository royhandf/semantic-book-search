from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
import spacy
import nltk

# download resources
nltk.download('stopwords')
nltk.download('wordnet')

db = SQLAlchemy()
csrf = CSRFProtect()

nlp = spacy.load('en_core_web_sm')