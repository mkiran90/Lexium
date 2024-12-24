
import math

from src.document.MetaIndex import MetaIndex
from src.forward_index.ForwardIndex import ForwardIndex

'''
BM25 NEEDS:
    - Term frequency
    - doc length
    - avg doc length
    - IDF:
        - no. of documents containing the term (t)
        - total number of documents
    - k1 (TF saturation constant)
    - b (doc. length normalization constant)
    - boost (title or tag)

Method of retrieval:

    - Term frequency: inverted index
    - doc. length: fwd index
    - avg doc length: metadata
    - no. of documents containing the term (t): inverted index
    - total no. of documents: metadata
'''

# open and close
meta_index = MetaIndex()
forward_index = ForwardIndex()
doc_count = forward_index.size()
avg_doc_length = meta_index.total_word_count() / doc_count
del meta_index, forward_index

k1 = 1.2
b = 0.75

def _idf(word_presence):
    doc_freq = len(word_presence.docSet)  # Number of documents the word appears in
    return math.log( ((doc_count - doc_freq + 0.5) / (doc_freq + 0.5)) + 1.0)

def _term_bm25(presence, term_idf, docID, doc_len):
    f = presence.docMap[docID].body_frequency()
    term_score = term_idf * ((f * (k1 + 1)) / (f + k1 * (1 - b + (b * (doc_len / avg_doc_length)))))

    return term_score

def get_bm25_score(presenceMap, idf_map, docID, doc_meta):
    # Calculate BM25 score for a document for a given query (now works with wordID directly)
    score = 0
    doc_len = doc_meta.body_length

    for (wordID, presence) in presenceMap.items():
       term_score = _term_bm25(presence, idf_map[wordID], docID, doc_len)

       score += term_score

    return score
