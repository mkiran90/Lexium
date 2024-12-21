import json
import math
from turtledemo.sorting_animate import start_ssort

from code.inverted_index.InvertedIndex import InvertedIndex
from code.inverted_index.Barrel import Barrel
from code.Ranking.MetaData import MetadataHandler
from code.forward_index.ForwardIndex import ForwardIndex


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
metadata_handler = MetadataHandler(forward_index)


# Load metadata (this will either load from the file or compute new metadata)
metadata_path = "C:\\Users\\user\\Documents\\GitHub\\Search-Engine\\code\\Ranking\\metadata.json"
with open(metadata_path, "r") as file:
    metadata = json.load(file)  # This will now be a dictionary


if metadata is None:
    metadata = {"avg_doc_length": 406.23601393082987, "doc_count": 190082}  # Use default if metadata is None

avg_doc_length = metadata.get("avg_doc_length", 406.23601393082987)
doc_count = metadata.get("doc_count", 190082)
k1 = 1.2
b = 0.75
title_boost = 1.5
tag_boost = 2.0


def _idf(wordID):
    # Calculate the inverse document frequency (IDF) for the word
    word_presence = inverted_index.get(wordID)
    doc_freq = len(word_presence.docSet)  # Number of documents the word appears in
    return math.log((doc_count - doc_freq + 0.5) / (doc_freq + 0.5) + 1.0)

def _doc_len(docID):
    document = forward_index.get_document(docID)
    return document.word_count()

def _term_freq_in_doc(wordID, docID):
    # Count the frequency of the word in the document
    term_freq = 0
    word_presence = inverted_index.get(wordID)
    term_freq = word_presence.count_doc(docID)
    return term_freq

def _get_title_and_tags(docID):
    # Assume metadata contains title and tags for each document
    # Replace this with your method of fetching the title and tags from the document metadata
    document_metadata = inverted_index.get_document_metadata(docID)
    title = document_metadata.get("title", "")
    tags = document_metadata.get("tags", [])
    return title, tags

def get_bm25_score(query_wordIDs, docID):
    # Calculate BM25 score for a document for a given query (now works with wordID directly)
    score = 0
    doc_len = _doc_len(docID)

    # Get the title and tags for the current document
    title, tags = _get_title_and_tags(docID)

    for wordID in query_wordIDs:  # Now query is a list of wordIDs directly
        idf = _idf(wordID)
        f = _term_freq_in_doc(wordID, docID)
        term_score = idf * (
                    (f * (k1 + 1)) / (f + k1 * (1 - b + b * doc_len / avg_doc_length)))

        # Boost score if word appears in title or tags
        if str(wordID) in title:
            term_score *= title_boost  # Apply title boost
        if str(wordID) in tags:
            term_score *= tag_boost  # Apply tag boost

        score += term_score

    return score
