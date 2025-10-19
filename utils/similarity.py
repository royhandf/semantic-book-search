from nltk.corpus import wordnet as wn

def wu_palmer_similarity(synset1, synset2):
    # mencari hipernym terendah yang sama
    lcs = synset1.lowest_common_hypernyms(synset2)
    if not lcs:
        return 0
    
    # ambil lcs pertama karena wordnet mengurutkan lcs berdasarkan urutan kedalaman
    lcs = lcs[0]
    
    # mengecek kedalaman LCS dan kedalaman masing-masing synset
    # makin dalam berarti makin spesifik
    depth_lcs = lcs.max_depth()
    depth_synset1 = synset1.max_depth()
    depth_synset2 = synset2.max_depth()
    
    # cek kalo root sama atau tidak ada hipernim maka 0
    denominator = depth_synset1 + depth_synset2
    if denominator == 0:
        return 0
        
    return (2 * depth_lcs) / denominator

def get_synsets(word):
    synsets = wn.synsets(word, pos=wn.NOUN) + wn.synsets(word, pos=wn.VERB) + wn.synsets(word, pos=wn.ADJ) + wn.synsets(word, pos=wn.ADV)
    return synsets if synsets else []

def calculate_similarity(query, book):
    query_synsets = get_synsets(query)
    book_synsets = get_synsets(book)

    if not query_synsets or not book_synsets:
        return 0

    best_similarity = 0

    for synset1 in query_synsets:
        for synset2 in book_synsets:
            try:
                similarity = wu_palmer_similarity(synset1, synset2)
                if similarity > best_similarity:
                    best_similarity = similarity
            except Exception as e:
                # print(f"Error calculating similarity between {synset1} and {synset2}: {str(e)}")
                continue

    return best_similarity
