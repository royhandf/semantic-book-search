import re
from extensions import nlp
from functools import lru_cache

def preprocessing(text):
    # Hapus URL, akronim besar, angka, karakter non-alfanumerik, angka Romawi, dan kata satu karakter
    text = re.sub(r'http\S+|www\S+|https\S+|\b[A-Z]{2,}(?:-[A-Z]+)+\b|\d+|\b\w\b|[IVXLCDM]+|\W+', ' ', text, flags=re.MULTILINE)
    text = text.lower()  # Ubah teks ke huruf kecil
    text = re.sub(r'\s+', ' ', text).strip()  # Hapus spasi berlebih dan strip spasi di awal/akhir
    
    # Gunakan nlp hanya sekali
    doc = nlp(text)
    # Tokenisasi dan lemmatization dalam satu langkah
    lemmatized_tokens = [token.lemma_ for token in doc if not token.is_stop and token.text.strip()]
    
    return lemmatized_tokens

# Cache untuk preprocessing
@lru_cache(maxsize=1000)
def cached_preprocessing(text):
    return preprocessing(text)