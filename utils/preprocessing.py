import re
import json
from extensions import nlp
from extensions import redis_client
import hashlib
import lemminflect

CLEAN_PATTERN = re.compile(r'\d+|\b\w\b|\W+|\b[A-Z]{2,}(?:-[A-Z]+)+\b', flags=re.MULTILINE)

def preprocessing(text):
    text = CLEAN_PATTERN.sub(' ', text.lower()).strip()
    text = re.sub(r'\s+', ' ', text)

    doc = nlp(text)
    
    lemmatized_tokens = []
    for token in doc:
        if not token.is_stop and token.text.strip():
            lemmas = lemminflect.getAllLemmas(token.text)
            if 'NOUN' in lemmas: 
                lemmatized_tokens.append(lemmas['NOUN'][0])  
            else:
                lemmatized_tokens.append(token.text)  
    return lemmatized_tokens

def cached_preprocessing(text):
    redis_key = hashlib.sha256(text.encode('utf-8')).hexdigest()

    cached_result = redis_client.get(redis_key)
    if cached_result:
        return json.loads(cached_result)

    result = preprocessing(text)
    
    with redis_client.pipeline() as pipe:
        pipe.set(redis_key, json.dumps(result), ex=None)
        pipe.execute()
        
    return result
