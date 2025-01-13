import re
import json
from extensions import nlp
from extensions import redis_client
import hashlib

CLEAN_PATTERN = re.compile(r'\d+|\b\w\b|[IVXLCDM]+|\W+|\b[A-Z]{2,}(?:-[A-Z]+)+\b', flags=re.MULTILINE)

def preprocessing(text):    
    text = CLEAN_PATTERN.sub(' ', text.lower()).strip()
    text = re.sub(r'\s+', ' ', text)

    doc = nlp(text)
    lemmatized_tokens = [token.lemma_ for token in doc if not token.is_stop and token.text.strip()]
    return lemmatized_tokens

def cached_preprocessing(text):
    redis_key = hashlib.sha256(text.encode('utf-8')).hexdigest()

    cached_result = redis_client.get(redis_key)
    if cached_result:
        return json.loads(cached_result)

    result = preprocessing(text)

    with redis_client.pipeline() as pipe:
        pipe.set(redis_key, json.dumps(result), ex=86400)
        pipe.execute()
        
    return result
