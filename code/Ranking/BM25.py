
import math

from code.document.DocumentMetadata import DocumentMetadata
from code.forward_index.ForwardIndex import ForwardIndex

# TODO: calculate IDF once at the start

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
document_metadata = DocumentMetadata()
forward_index = ForwardIndex()


doc_count = forward_index.size()
avg_doc_length = document_metadata.total_word_count() / doc_count
k1 = 1.2
b = 0.75

def _idf(word_presence):
    doc_freq = len(word_presence.docSet)  # Number of documents the word appears in
    return math.log( ((doc_count - doc_freq + 0.5) / (doc_freq + 0.5)) + 1.0)

def _term_bm25(presence, docID, doc_len):
    idf = _idf(presence)
    f = presence.docMap[docID].body_frequency()
    term_score = idf * ((f * (k1 + 1)) / (f + k1 * (1 - b + (b * (doc_len / avg_doc_length)))))

    return term_score

def get_bm25_score(presenceMap, docID):
    # Calculate BM25 score for a document for a given query (now works with wordID directly)
    score = 0
    doc_len = document_metadata.get_doc_length(docID)

    for (wordID, presence) in presenceMap.items():
       term_score = _term_bm25(presence, docID, doc_len)

       score += term_score

    return score
