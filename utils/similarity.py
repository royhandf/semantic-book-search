from nltk.corpus import wordnet as wn

def wu_palmer_similarity(synset1, synset2):
    lcs = synset1.lowest_common_hypernyms(synset2)
    if not lcs:
        return 0
    
    lcs = lcs[0]
    
    depth_lcs = lcs.max_depth()
    depth_synset1 = synset1.max_depth()
    depth_synset2 = synset2.max_depth()
    
    return (2 * depth_lcs) / (depth_synset1 + depth_synset2)

def get_synsets(word):
    synsets = wn.synsets(word, pos=wn.NOUN) + wn.synsets(word, pos=wn.VERB) + wn.synsets(word, pos=wn.ADJ)
    if not synsets:
        return None  
    return synsets

def calculate_similarity(query, book):
    query_synsets = get_synsets(query)
    book_synsets = get_synsets(book)

    if not query_synsets or not book_synsets:
        return 0

    best_similarity = 0

    for synset1 in query_synsets:
        for synset2 in book_synsets:
            similarity = wu_palmer_similarity(synset1, synset2)
            best_similarity = max(best_similarity, similarity)  # Pilih kemiripan tertinggi

    return best_similarity
