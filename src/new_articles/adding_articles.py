import time
import numpy as np
from newspaper import Article


from src.preprocessing.data_cleaning import clean_body, clean_title, clean_tags

from src.util.util_functions import get_position_map,get_word_vector
from src.document.Document import Document, DocumentBodyWord

from src.inverted_index.WordPresence import WordInDoc


class ArticleAddition:

    def __init__(self, lexicon,fwd_index,inv_index,result_meta,model,word_embedding,rank_meta,nlp):
        self.fwd_index = fwd_index
        self.inv_index = inv_index
        self.lexicon = lexicon
        self.result_meta = result_meta
        self.rank_meta = rank_meta
        self.word_embedding = word_embedding
        self.model = model
        self.nlp = nlp


    def valid_title(self, title: str):
        return len(title.strip()) > 0 and len(title.split()) > 1

    def valid_body(self,body: str):
        # AT LEAST 30 WORDS
        return len(body.split()) > 30

    def download_with_retries(self,article, retries=10):
        while retries > 0:
            try:
                article.download()
                article.throw_if_not_downloaded_verbose()
                return
            except:
                retries -= 1
                time.sleep(0.1)

        raise Exception("FAILURE TO DOWNLOAD HTML")

    def _parse_url(self,url: str):
        article = Article(url)
        self.download_with_retries(article)
        article.parse()
        return article.title, article.tags, article.text, article.top_img

    def _generate_WordInDocMap(self,title_words, body_words):
        wordInDoc_map = {}

        for (wordID, body_positions) in body_words.items():
            wordInDoc_map[wordID] = WordInDoc([], body_positions)

        for (i, wordID) in enumerate(title_words):

            try:
                wordInDoc_map[wordID].title_positions.append(i)
            except KeyError:
                wordInDoc_map[wordID] = WordInDoc([i], [])

        return wordInDoc_map

    # ALL UPDATES REGARDING LEXICON AND WORDEMBEDDING
    def handle_words(self,cleaned_title, cleaned_tags, cleaned_text):
        title_wordIDs = []
        tag_wordIDs = []
        body_wordIDs = []

        for word in cleaned_title:
            wordID, new = self.lexicon.get_or_assign(word)
            vec = get_word_vector(word, self.model)
            if new:
                self.word_embedding.add_word_embedding(wordID, vec)
            title_wordIDs.append(wordID)

        for word in cleaned_tags:
            wordID, new = self.lexicon.get_or_assign(word)
            vec = get_word_vector(word, self.model)
            if new:
                self.word_embedding.add_word_embedding(wordID, vec)
            tag_wordIDs.append(wordID)

        body_meaning = np.zeros(shape=(300,))

        for word in cleaned_text:
            wordID, new = self.lexicon.get_or_assign(word)
            vec = get_word_vector(word, self.model)
            if new:
                self.word_embedding.add_word_embedding(wordID, vec)
            body_wordIDs.append(wordID)
            body_meaning += vec

        body_meaning = (body_meaning / len(body_wordIDs)).astype(np.float32)

        return title_wordIDs, tag_wordIDs, body_wordIDs, body_meaning

    def _generate_structures(self,title, tags, body):
        cleaned_title: list = clean_title(title, self.nlp, for_csv=False)
        cleaned_tags: list = clean_tags(tags, for_csv=False)
        cleaned_text: list = clean_body(body, self.nlp, for_csv=False)

        # LEXICON AND WORD-EMBEDDING UPDATES
        title_wordIDs, tag_wordIDs, body_wordIDs, body_meaning = self.handle_words(cleaned_title, cleaned_tags, cleaned_text)

        pos_map = get_position_map(body_wordIDs)

        body_words = [DocumentBodyWord(wordID, positions) for wordID, positions in
                      pos_map.items()]

        doc = Document(title_wordIDs, tag_wordIDs, body_words)
        wordInDoc_map = self._generate_WordInDocMap(title_wordIDs, pos_map)

        return doc, wordInDoc_map, body_meaning

    def add_article(self,url: str):

        A = time.time()
        title, tags, body, img_url = self._parse_url(url)
        print("Url parsed successfully", time.time() - A)

        if not (self.valid_body(body) and self.valid_title(title)):
            raise Exception("INVALID ARTICLE, WILL NOT INDEX")

        A = time.time()
        # LEXICON AND WORD EMBEDDING UPDATES
        doc, wordInDoc_map, body_meaning = self._generate_structures(title, tags, body)
        print("Updated lexicon and word embeddings", time.time() - A)

        A = time.time()
        # FORWARD INDEX AND RESULT_META UPDATES
        assigned_docID_1 = doc.store(self.fwd_index)
        assigned_docID_2 = self.result_meta.store(url=url,img_url=img_url, title=title)

        # ensure integrity
        assert assigned_docID_1 == assigned_docID_2, "Disparity between fwd index and urldict docID"

        print("Updated Forward index and docurldict", time.time() - A)

        A = time.time()
        # RANK_META UPDATE
        assigned_docID = self.rank_meta.add_doc_metadata(len(doc.title_words), doc.doc_length(), body_meaning)
        assert assigned_docID_1 == assigned_docID, "Disparity between metadata assigned docID and actual docID"

        print("Updated metadata", time.time() - A)

        A = time.time()
        # INVERTED INDEX UPDATE
        self.inv_index.index_document(assigned_docID, doc_wordInDocs=wordInDoc_map)
        print("Updated Inverted Index", time.time() - A)

    def add_with_content(self, title, body, tags, url):
        pass

    def placeholder_add(self, url):
        if url:
            return True
        else:
            return False

    def placeholder_add_with_content(self, title, body,  url):
        if url:
            return True
        else:
            return False


if __name__ == "__main__":
    from src.meta.ResultMetaIndex import ResultMetaIndex
    from src.meta.RankingMetaIndex import RankingMetaIndex
    from src.forward_index.ForwardIndex import ForwardIndex
    from src.inverted_index.InvertedIndex import InvertedIndex
    from src.lexicon_gen.Lexicon import Lexicon
    from src.lexicon_gen.WordEmbedding import WordEmbedding
    from src.util.util_functions import get_nlp, get_word2vec

    lexicon = Lexicon()
    fwd_index = ForwardIndex()
    inv_index = InvertedIndex()
    result_meta = ResultMetaIndex()

    model = get_word2vec()
    word_embedding = WordEmbedding()
    rank_meta = RankingMetaIndex()
    nlp = get_nlp()

    Adder = ArticleAddition(lexicon, fwd_index, inv_index, result_meta, model, word_embedding, rank_meta, nlp)

    while True:
        url = input("Enter URL: ")
        if url == "exit":
            break
        try:
            Adder.add_article(url)
            print("Indexed Successfully.")
        except:
            print("Couldnt Index")

    lexicon.save_lexicon()