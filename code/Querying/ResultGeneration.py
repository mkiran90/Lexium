from itertools import combinations

from code.Ranking.BM25 import get_bm25_score
from code.Ranking.Proximity import get_proximity_score
from code.forward_index.ForwardIndex import ForwardIndex
from code.inverted_index.InvertedIndex import InvertedIndex
from code.lexicon_gen.Lexicon import Lexicon
from code.document.DocURLDict import DocURLDict

inverted_index = InvertedIndex()
forward_index = ForwardIndex()
lexicon = Lexicon()
urlDict = DocURLDict()
class ResultGeneration:

    def __init__(self, query):
        self.query = query
        words = self.query.split()
        self.query_word_ids = set([lexicon.get(word) for word in words if lexicon.get(word) is not None])
        self.presenceMap = {}
        self._populate_presenceMap()

    def _populate_presenceMap(self):

        # TODO: make sure each wordID is indexed first so assertion never fails

        for wordID in self.query_word_ids:
            presence = inverted_index.get(wordID)
            assert presence is not None
            self.presenceMap[wordID] = presence

    def _relevant_docs(self):

        # it is an empirical fact that a greater wordID has a smaller doclist
        # and intersection of sets is O(min(m,n)) where m and n is size of sets that are being intersected
        # starting with the smallest is the fastest way to go about this

        max_wordID = max(self.query_word_ids)
        result_set = self.presenceMap[max_wordID].docSet
        for wordID in self.query_word_ids:
            if wordID == max_wordID:
                continue
            result_set = result_set & self.presenceMap[wordID].docSet

        return result_set


    def _get_total_doc_score(self, doc_id):

        # TODO: load document's clean body text using clean csv
        # document_word_ids = [body_word.wordID for body_word in forward_index.get_document(doc_id).body_words]

        score = 0
        score += get_bm25_score(self.presenceMap, doc_id)
        # score += 0.25 * get_semantic_score(self.query, document)
        if len(self.query_word_ids) > 1:
            score += get_proximity_score(self.presenceMap, doc_id)

        return score

    def get_search_results(self):

        # word_count = len(self.query_word_ids)
        #
        # if word_count == 0:
        #     return set()
        #
        # doc_sets = [inverted_index.get(word_id).docSet for word_id in self.query_word_ids]
        #
        # if not doc_sets:
        #     return set()
        #
        # overall_result_set: set = doc_sets[0].copy()
        #
        # for doc_set in doc_sets[1:]:
        #     overall_result_set.intersection_update(doc_set)
        #
        #
        # while not overall_result_set:
        #     word_count -= 1
        #     query_combinations = [set(combination) for combination in combinations(self.query_word_ids, word_count)]
        #
        #     for combination in query_combinations:
        #         doc_sets = [inverted_index.get(word_id).docSet for word_id in combination]
        #         result_set = doc_sets[0].copy()
        #
        #         for doc_set in doc_sets[1:]:
        #             result_set.intersection_update(doc_set)
        #
        #         overall_result_set.union(result_set)


        relevant_doc_ids = self._relevant_docs()
        sorted_doc_id_list = self._rank_documents(relevant_doc_ids)
        return [(docID,urlDict.get_url(docID)) for docID in sorted_doc_id_list]

    def _rank_documents(self, doc_id_list: set):
        scores = {}

        for doc_id in doc_id_list:
            scores[doc_id] = self._get_total_doc_score(doc_id)

        sorted_scores = sorted(scores.items(), key=lambda item: item[1], reverse=True)

        return [score[0] for score in sorted_scores]
