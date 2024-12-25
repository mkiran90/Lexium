import numpy as np
import Levenshtein

from src.ranking.BM25 import get_bm25_score,_idf
from src.ranking.Proximity import get_body_prox_score, get_title_prox_score
from src.ranking.Semantic import get_semantic_score
from src.ranking.TitleScore import get_title_score
from src.document.MetaIndex import MetaIndex
from src.forward_index.ForwardIndex import ForwardIndex
from src.inverted_index.InvertedIndex import InvertedIndex
from src.lexicon_gen.Lexicon import Lexicon
from src.document.DocURLDict import DocURLDict
from src.lexicon_gen.WordEmbedding import WordEmbedding
from src.preprocessing.data_cleaning import clean_title
from src.util.util_functions import get_nlp


# THESE SHOULD BE LOADED AS APP STARTS UP, OR AS SERVER STARTS
nlp = get_nlp()
inverted_index = InvertedIndex()
forward_index = ForwardIndex()
lexicon = Lexicon()
urlDict = DocURLDict()
meta_index = MetaIndex()
word_embedding = WordEmbedding()

class ResultGeneration:

    def __init__(self, query):
        self.query = query
        self.clean_query_words = clean_title(query, nlp,for_csv=False)
        self.query_word_ids = set([lexicon.get(word) for word in self.clean_query_words if lexicon.get(word) is not None])
        self.query_meaning = self.get_query_meaning()
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

    def _generate_docmeta_map(self, doc_list):
        return meta_index.batch_load(doc_list)

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

    def _get_total_doc_score(self, doc_id, doc_meta):

        body_freq = get_bm25_score(self.presence_map, self.idf_map, doc_id, doc_meta=doc_meta)
        body_prox = get_body_prox_score(self.presence_map, doc_id)
        body = body_freq * body_prox

        title_freq = get_title_score(self.presence_map, doc_id, doc_meta=doc_meta)
        title_prox = get_title_prox_score(self.presence_map, doc_id)
        title = title_freq * title_prox
        semantic = get_semantic_score(self.query_meaning, doc_meta=doc_meta)

        return 0.2*body + 0.6*title + 0.2*semantic

    def get_search_results(self):
        relevant_doc_ids = self._relevant_docs()
        sorted_doc_id_list = self._rank_documents(relevant_doc_ids)
        return [(docID,urlDict.get(docID)) for docID in sorted_doc_id_list]

    def _rank_documents(self, doc_id_list: set):
        docmeta_map = self._generate_docmeta_map(doc_id_list)
        scores = {doc_id : self._get_total_doc_score(doc_id, docmeta_map[doc_id]) for doc_id in doc_id_list}
        sorted_scores = sorted(scores.items(), key=lambda item: item[1], reverse=True)

        return [score[0] for score in sorted_scores]

    def get_query_meaning(self):
        vec_sum = np.zeros(shape=(300,))

        if len(self.query_word_ids) == 0:
            query_embedding = vec_sum
        else:
            for word_id in self.query_word_ids:
                vec = word_embedding.get_word_embedding(word_id)

                if vec is not None:
                    vec_sum += vec

            query_embedding = (vec_sum / len(self.query_word_ids)).astype(np.float32)

        return query_embedding
    
    def _correct_query_words(self):

        #getting the corrected query, will be as Did you mean "corrected_words"
        corrected_words = []
        
        for word in self.query:
        
            word_id = lexicon.get(word)
            
            if word_id is None: 
               
                lexicon_words = [word for word in lexicon._lexicon]
                closest_match = min(lexicon_words, key=lambda x: Levenshtein.distance(word, x))
                corrected_words.append(closest_match)
            else:
                corrected_words.append(word)
        
        return corrected_words
    
    def get_search_docIDs(self):

        # getting docIDs first
        # helps in paging (then get the URLs according to the docID in the page ) 
        relevant_doc_ids = self._relevant_docs()
        sorted_doc_id_list = self._rank_documents(relevant_doc_ids)
        return sorted_doc_id_list
    
    
    