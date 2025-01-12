import re
from extensions import nlp
import json
from extensions import redis_client
import hashlib

CLEAN_PATTERN = re.compile(r'\d+|\b\w\b|[IVXLCDM]+|\W+|\b[A-Z]{2,}(?:-[A-Z]+)+\b', flags=re.MULTILINE)

def preprocessing(text):    
    text = CLEAN_PATTERN.sub(' ', text.lower()).strip()
    text = re.sub(r'\s+', ' ', text)

    # Gunakan SpaCy untuk lemmatization
    doc = nlp(text)
    lemmatized_tokens = [token.lemma_ for token in doc if not token.is_stop and token.text.strip()]
    return lemmatized_tokens

def generate_redis_key(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

# Cache preprocessing
def cached_preprocessing(text):
    # Buat Redis key dari hash teks
    redis_key = generate_redis_key(text)

    # Cek apakah teks sudah ada di Redis
    cached_result = redis_client.get(redis_key)
    if cached_result:
        return json.loads(cached_result)

    # Jika tidak ada, lakukan preprocessing
    result = preprocessing(text)

    # Simpan hasil ke Redis
    redis_client.set(redis_key, json.dumps(result), ex=3600)  # TTL 1 jam
    return result

