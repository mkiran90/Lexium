import threading
import time
from collections import Counter

import numpy as np
import Levenshtein
from src.ranking.BM25 import get_bm25_score,_idf
from src.ranking.Proximity import get_body_prox_score, get_title_prox_score
from src.ranking.Semantic import get_semantic_score
from src.ranking.TitleScore import get_title_score
from src.preprocessing.data_cleaning import clean_title

class ResultGeneration:

    def __init__(self, query, nlp,inverted_index,forward_index,lexicon,resultMeta,rankMeta,word_embedding):
        self.forward_index = forward_index
        self.inverted_index = inverted_index
        self.lexicon = lexicon
        self.resultMeta = resultMeta
        self.rankMeta = rankMeta
        self.word_embedding = word_embedding
        self.query = query
        self.clean_query_words = clean_title(query, nlp,for_csv=False)
        self.query_word_ids = set([self.lexicon.get(word) for word in self.clean_query_words if self.lexicon.get(word) is not None])
        self.query_meaning = self.get_query_meaning()
        self.presence_map = self._generate_presence_map()
        self.idf_map = self._generate_idf_map()

    def _generate_presence_map(self):

        presence_map = {}

        lock = threading.Lock()

        def get_presence(wordID):
            presence = self.inverted_index.get(wordID)
            with lock:
                presence_map[wordID] = presence

        threads = []

        for wordID in self.query_word_ids:
            thread = threading.Thread(target=get_presence, args=(wordID,))
            threads.append(thread)
            thread.start()
        for thread in threads:
            thread.join()

        return presence_map

    def _generate_idf_map(self):

        idf_map = {}
        for wordID in self.query_word_ids:
            idf_map[wordID] = _idf(self.presence_map[wordID])

        return idf_map

    def _generate_docmeta_map(self, doc_list):
        return self.rankMeta.batch_load(doc_list)


    def _relevant_docs(self):

        doc_occurrence = Counter()

        reverse_index = {i : [] for i in range(1, len(self.query_word_ids) + 1)}

        for wordID in self.query_word_ids:
            doc_occurrence.update(self.presence_map[wordID].docSet)
        for docID, count in doc_occurrence.items():
            reverse_index[count].append(docID)

        del doc_occurrence

        relevant_docs = set()


        n = len(self.query_word_ids)
        while len(relevant_docs) < 100 and n > 0:
            relevant_docs.update(reverse_index[n])
            n -= 1

        return relevant_docs

    def _get_total_doc_score(self, doc_id, doc_meta):

        body_freq = get_bm25_score(self.presence_map, self.idf_map, doc_id, doc_meta=doc_meta)
        body_prox = get_body_prox_score(self.presence_map, doc_id)
        body = body_freq * body_prox

        title_freq = get_title_score(self.presence_map, doc_id)
        title_prox = get_title_prox_score(self.presence_map, doc_id)
        title = title_freq * title_prox
        semantic = get_semantic_score(self.query_meaning, doc_meta=doc_meta)

        return 0.20*body + 0.75*title + 0.05*semantic

    def get_search_results(self):

        if len(self.query_word_ids) == 0:
            return []

        A = time.time()
        relevant_doc_ids = self._relevant_docs()
        print("Time collecting relevant docs: ", time.time() - A, "Num Docs: ", len(relevant_doc_ids))
        A = time.time()
        sorted_doc_id_list = self._rank_documents(relevant_doc_ids)
        print("Time ranking and sorting: ", time.time() - A)
        A = time.time()
        
        # ONLY TOP 100
        # here info is a [url, img_url, title]
        print(sorted_doc_id_list)
        docId_info = [self.resultMeta.get(docID) for docID in sorted_doc_id_list[:100]]
        print("Time fetching URLs: ", time.time() - A)
        return docId_info

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
                vec = self.word_embedding.get_word_embedding(word_id)

                if vec is not None:
                    vec_sum += vec

            query_embedding = (vec_sum / len(self.query_word_ids)).astype(np.float32)

        return query_embedding
    
    def _correct_query_words(self):
    # Getting the corrected query, will be used as "Did you mean 'corrected_words'?"
     corrected_words = []


     for word in self.query.split():
        word_id = self.lexicon.get(word)
        
        if word_id is None: 
            # If word is not found in the lexicon, find the closest match
            lexicon_words = [word for word in self.lexicon._lexicon]
            closest_match = min(lexicon_words, key=lambda x: Levenshtein.distance(word, x))
            corrected_words.append(closest_match)
        else:
            # If word is found, keep it unchanged
            corrected_words.append(word)
    
     return corrected_words
    
    def get_search_docIDs(self):

        # getting docIDs first
        # helps in paging (then get the URLs according to the docID in the page ) 
        relevant_doc_ids = self._relevant_docs()
        sorted_doc_id_list = self._rank_documents(relevant_doc_ids)
        return sorted_doc_id_list
    
    
    
