
import math

from code.inverted_index.InvertedIndex import InvertedIndex
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

forward_index = ForwardIndex()
inverted_index = InvertedIndex()
# metadata_handler = MetadataHandler(forward_index)
#
#
# # Load metadata (this will either load from the file or compute new metadata)
# metadata_path = "C:\\Users\\user\\Documents\\GitHub\\Search-Engine\\code\\Ranking\\metadata.json"
# with open(metadata_path, "r") as file:
#     metadata = json.load(file)  # This will now be a dictionary
#
#
# if metadata is None:
#     metadata = {"avg_doc_length": 406.23601393082987, "doc_count": 190082}  # Use default if metadata is None

# avg_doc_length = metadata.get("avg_doc_length", 406.23601393082987)
# doc_count = metadata.get("doc_count", 190082)

avg_doc_length = 406.236
doc_count = 190082

k1 = 1.2
b = 0.75

# 0.1  = 10% boost per occurrence of word in title
title_multiplier = 0.1
title_constant = 1

def _idf(word_presence):
    doc_freq = len(word_presence.docSet)  # Number of documents the word appears in
    return math.log( ((doc_count - doc_freq + 0.5) / (doc_freq + 0.5)) + 1.0)

def _doc_len(docID):
    return 300

def _body_frequency(word_presence, docID):
    return word_presence.docMap[docID].body_frequency()
def _title_frequency(word_presence, docID):
    return word_presence.docMap[docID].title_frequency()

def _term_bm25(presence, docID, doc_len):
    idf = _idf(presence)
    f = _body_frequency(presence, docID)
    term_score = idf * (
            (f * (k1 + 1)) / (f + k1 * (1 - b + (b * (doc_len / avg_doc_length)))))
    return term_score

def get_bm25_score(presenceMap, docID):
    # Calculate BM25 score for a document for a given query (now works with wordID directly)
    score = 0
    doc_len = _doc_len(docID)

    for (wordID, presence) in presenceMap.items():

       term_score = _term_bm25(presence, docID, doc_len)

       # boost by 10% per time the word occurs in title
       term_score += (title_constant*_title_frequency(presence, docID))

       score += term_score

    return score
