import time

from code.Ranking.BM25 import get_bm25_score,_idf
from code.Ranking.Proximity import get_body_prox_score, get_title_prox_score
from code.Ranking.Semantic import get_semantic_score
from code.Ranking.TitleScore import get_title_score
from code.document.DocumentMetadata import DocumentMetadata
from code.forward_index.ForwardIndex import ForwardIndex
from code.inverted_index.InvertedIndex import InvertedIndex
from code.lexicon_gen.Lexicon import Lexicon
from code.document.DocURLDict import DocURLDict
from code.lexicon_gen.WordEmbedding import WordEmbedding
from code.preprocessing import data_cleaning

inverted_index = InvertedIndex()
forward_index = ForwardIndex()
lexicon = Lexicon()
urlDict = DocURLDict()
document_metadata = DocumentMetadata()
word_embedding = WordEmbedding()
class ResultGeneration:

    def __init__(self, query):
        self.query = data_cleaning.clean_title(query)
        self.query = self.query.split()
        self.query_word_ids = set([lexicon.get(word) for word in self.query if lexicon.get(word) is not None])
        self.presence_map = self._generate_presence_map()
        self.idf_map = self._generate_idf_map()

    def _generate_presence_map(self):

        # TODO: make sure each wordID is indexed first so assertion never fails

        presence_map = {}
        for wordID in self.query_word_ids:
            presence = inverted_index.get(wordID)
            assert presence is not None
            presence_map[wordID] = presence
        return presence_map

    def _generate_idf_map(self):

        idf_map = {}
        for wordID in self.query_word_ids:
            idf_map[wordID] = _idf(self.presence_map[wordID])

        return idf_map


    def _relevant_docs(self):

        # it is an empirical fact that a greater wordID has a smaller doclist
        # and intersection of sets is O(min(m,n)) where m and n is size of sets that are being intersected
        # starting with the smallest is the fastest way to go about this

        max_wordID = max(self.query_word_ids)
        result_set = self.presence_map[max_wordID].docSet
        for wordID in self.query_word_ids:
            if wordID == max_wordID:
                continue
            result_set = result_set & self.presence_map[wordID].docSet

        return result_set

    def _get_total_doc_score(self, doc_id):

        score = 0.25 * get_bm25_score(self.presence_map, self.idf_map, doc_id, document_metadata) * get_body_prox_score(self.presence_map, doc_id)
        score += 0.45 * get_title_score(self.presence_map, doc_id) * get_title_prox_score(self.presence_map, doc_id)
        score += 0.3 * get_semantic_score(self.query_word_ids, doc_id, word_embedding, document_metadata)

        return score

    def get_search_results(self):
        relevant_doc_ids = self._relevant_docs()
        sorted_doc_id_list = self._rank_documents(relevant_doc_ids)
        return [(docID,urlDict.get(docID)) for docID in sorted_doc_id_list]

    def _rank_documents(self, doc_id_list: set):
        scores = {doc_id : self._get_total_doc_score(doc_id) for doc_id in doc_id_list}
        sorted_scores = sorted(scores.items(), key=lambda item: item[1], reverse=True)

        return [score[0] for score in sorted_scores]


