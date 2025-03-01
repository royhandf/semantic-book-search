import re
import json
from extensions import nlp
from extensions import redis_client
import hashlib
import lemminflect

CLEAN_PATTERN = re.compile(r'\d+|\b\w\b|[IVXLCDM]+|\W+|\b[A-Z]{2,}(?:-[A-Z]+)+\b', flags=re.MULTILINE)

def preprocessing(text):    
    text = CLEAN_PATTERN.sub(' ', text.lower()).strip()
    text = re.sub(r'\s+', ' ', text)

    doc = nlp(text)
    
    lemmatized_tokens = []
    for token in doc:
        if not token.is_stop and token.text.strip():
            lemmas = lemminflect.getAllLemmas(token.text)
            if 'NOUN' in lemmas:  # Gunakan bentuk lemma sebagai NOUN jika tersedia
                lemmatized_tokens.append(lemmas['NOUN'][0])  # Ambil bentuk pertama
            else:
                lemmatized_tokens.append(token.text)  # Fallback ke teks asli
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
