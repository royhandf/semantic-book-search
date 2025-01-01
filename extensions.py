from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import spacy
import nltk
import redis

# download resources
nltk.download('stopwords')
nltk.download('wordnet')

db = SQLAlchemy()
login_manager = LoginManager()

nlp = spacy.load('en_core_web_sm')

redis_client = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)
