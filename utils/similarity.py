from nltk.corpus import wordnet as wn

def wu_palmer_similarity(synset1, synset2):
    similarity = synset1.wup_similarity(synset2)
    if similarity is None:
        return 0  
    return similarity

def get_synsets(word):
    """Mendapatkan synset dari kata hanya untuk POS noun, verb, dan adj."""
    return (
        wn.synsets(word, pos=wn.NOUN) + 
        wn.synsets(word, pos=wn.VERB) + 
        wn.synsets(word, pos=wn.ADJ)
    )

def calculate_similarity(query, book):
    """Menghitung kemiripan menggunakan Wu-Palmer dengan cache dan filter POS."""
    query_synsets = get_synsets(query)
    book_synsets = get_synsets(book)

    if not query_synsets or not book_synsets:
        return 0

    best_similarity = 0
    seen_pairs = set()

    for synset1 in query_synsets:
        for synset2 in book_synsets:
            pair = (synset1, synset2)
            if pair not in seen_pairs:
                similarity = wu_palmer_similarity(synset1, synset2)
                seen_pairs.add(pair)
                if similarity > best_similarity:
                    best_similarity = similarity

    return best_similarity
