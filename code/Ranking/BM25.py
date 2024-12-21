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

barrel = Barrel()
forward_index = ForwardIndex()
inverted_index = InvertedIndex()
metadata_handler = MetadataHandler(forward_index)

# Load metadata (this will either load from the file or compute new metadata)
metadata_path = "C:\\Users\\user\\Documents\\GitHub\\Search-Engine\\code\\Ranking\\metadata.json"
with open(metadata_path, "r") as file:
    metadata = json.load(file)  # This will now be a dictionary


class BM25:
    def _init_(self, inverted_index, forward_index, avg_doc_length, doc_count, metadata=None, title_boost=1.5, tag_boost=1.2):
        if metadata is None:
            metadata = {"avg_doc_length": avg_doc_length, "doc_count": doc_count}  # Use default if metadata is None
        self.avg_doc_length = metadata.get("avg_doc_length", 406.23601393082987)
        self.doc_count = metadata.get("doc_count", 190082)
        self.inverted_index = inverted_index
        self.forward_index = forward_index
        self.k1 = 1.2
        self.b = 0.75
        self.title_boost = title_boost
        self.tag_boost = tag_boost

    def _idf(self, wordID):
        # Calculate the inverse document frequency (IDF) for the word
        barrel_num, in_barrel_pos = self.inverted_index.get_position(wordID)
        if barrel_num <= 0:
            return 0  # Word not indexed, IDF is 0
        barrel = Barrel(barrel_num)
        word_presence = barrel.get(in_barrel_pos)
        doc_freq = len(word_presence.docSet)  # Number of documents the word appears in
        return math.log((self.doc_count - doc_freq + 0.5) / (doc_freq + 0.5) + 1.0)

    def _doc_len(self, docID):
        # Calculate the length of a document (number of terms)
        # doc_len = 0
        document = self.forward_index.get_document(docID)

        # for barrel_num in range(1, self.inverted_index.running_barrel_num() + 1):
        #     barrel = Barrel(barrel_num)
        #     for word_presence in barrel.get(in_barrel_pos)():
        #         if word_presence.has_doc(docID):
        #             doc_len += 1
        return document.word_count()

    def _term_freq_in_doc(self, wordID, docID):
        # Count the frequency of the word in the document
        term_freq = 0
        barrel_num, in_barrel_pos = self.inverted_index.get_position(wordID)
        if barrel_num <= 0:
            return 0
        barrel = Barrel(barrel_num)
        word_presence = barrel.get(in_barrel_pos)
        term_freq = word_presence.count_doc(docID)
        return term_freq

    def _get_title_and_tags(self, docID):
        # Assume metadata contains title and tags for each document
        # Replace this with your method of fetching the title and tags from the document metadata
        document_metadata = self.inverted_index.get_document_metadata(docID)
        title = document_metadata.get("title", "")
        tags = document_metadata.get("tags", [])
        return title, tags

    def calculate_score(self, query_wordIDs, docID):
        # Calculate BM25 score for a document for a given query (now works with wordID directly)
        score = 0
        doc_len = self._doc_len(docID)

        # Get the title and tags for the current document
        title, tags = self._get_title_and_tags(docID)

        for wordID in query_wordIDs:  # Now query is a list of wordIDs directly
            idf = self._idf(wordID)
            f = self._term_freq_in_doc(wordID, docID)
            term_score = idf * (
                        (f * (self.k1 + 1)) / (f + self.k1 * (1 - self.b + self.b * doc_len / self.avg_doc_length)))

            # Boost score if word appears in title or tags
            if str(wordID) in title:
                term_score *= self.title_boost  # Apply title boost
            if str(wordID) in tags:
                term_score *= self.tag_boost  # Apply tag boost

            score += term_score

        return score

    def rank_documents(self, query_wordIDs):
        # Rank documents based on BM25 score
        scores = {}
        for barrel_num in range(1, self.inverted_index.running_barrel_num() + 1):
            barrel = Barrel(barrel_num)
            for word_presence in barrel.get_all_word_presences():
                # Loop through all the documents containing the word
                for docID in word_presence.docSet:  # Get docIDs from word_presence
                    if docID not in scores:
                        scores[docID] = 0
                    scores[docID] += self.calculate_score(query_wordIDs, docID)

        # Sort the documents by BM25 score in descending order
        return sorted(scores.items(), key=lambda x: x[1], reverse=True)

    def calculate_word_relevance_for_all_docs(self, wordID):
        # Calculate BM25 relevance for all docs for a given wordID
        barrel_num, in_barrel_pos = self.inverted_index.get_position(wordID)
        if barrel_num <= 0:
            return []  # Word not indexed
        barrel = Barrel(barrel_num)
        word_presence = barrel.get(in_barrel_pos)

        # Loop through all the documents that contain the word and calculate BM25 score for each
        scores = {}
        for docID in word_presence.docSet:  # Automatically get docIDs from word_presence
            score = self.calculate_score([wordID], docID)  # Pass wordID directly
            scores[docID] = score

        # Return the documents ranked by BM25 score
        return sorted(scores.items(), key=lambda x: x[1], reverse=True)