import time
import traceback
import numpy as np
from newspaper import Article

from src.inverted_index.InvertedIndex import InvertedIndex
from src.preprocessing.data_cleaning import clean_body, clean_title, clean_tags
from src.lexicon_gen.Lexicon import Lexicon
from src.util.util_functions import get_position_map,get_word2vec, get_word_vector, get_nlp
from src.document.Document import Document, DocumentBodyWord
from src.document.DocURLDict import DocURLDict
from src.forward_index.ForwardIndex import ForwardIndex
from src.inverted_index.WordPresence import WordInDoc
from src.lexicon_gen.WordEmbedding import WordEmbedding
from src.document.MetaIndex import MetaIndex

lexicon = Lexicon()
fwd_index = ForwardIndex()
inv_index = InvertedIndex()
url_dict = DocURLDict()
model = get_word2vec()
word_embedding = WordEmbedding()
meta = MetaIndex()
nlp = get_nlp()


def valid_title(title:str):
    return len(title.strip()) > 0 and len(title.split()) > 1

def valid_body(body:str):
    # AT LEAST 30 WORDS
    return len(body.split()) > 30


def download_with_retries(article, retries = 10):
    while retries > 0:
        try:
            article.download()
            article.throw_if_not_downloaded_verbose()
            return
        except:
            retries -= 1
            time.sleep(0.1)

    raise Exception("FAILURE TO DOWNLOAD HTML")

def _parse_url(url:str):
    article = Article(url)
    download_with_retries(article)
    article.parse()
    return article.title, article.tags, article.text

def _generate_WordInDocMap(title_words, body_words):
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
def handle_words(cleaned_title, cleaned_tags, cleaned_text):
    title_wordIDs = []
    tag_wordIDs = []
    body_wordIDs = []

    for word in cleaned_title:
        wordID, new = lexicon.get_or_assign(word)
        vec = get_word_vector(word, model)
        if new:
            word_embedding.add_word_embedding(wordID, vec)
        title_wordIDs.append(wordID)

    for word in cleaned_tags:
        wordID, new = lexicon.get_or_assign(word)
        vec = get_word_vector(word, model)
        if new:
            word_embedding.add_word_embedding(wordID, vec)
        tag_wordIDs.append(wordID)

    body_meaning = np.zeros(shape=(300,))

    for word in cleaned_text:
        wordID, new = lexicon.get_or_assign(word)
        vec = get_word_vector(word, model)
        if new:
            word_embedding.add_word_embedding(wordID, vec)
        body_wordIDs.append(wordID)
        body_meaning += vec

    body_meaning = (body_meaning / len(body_wordIDs)).astype(np.float32)

    return title_wordIDs, tag_wordIDs, body_wordIDs, body_meaning

def _generate_structures(title, tags, body):
    cleaned_title:list = clean_title(title, nlp, for_csv=False)
    cleaned_tags:list = clean_tags(tags, for_csv=False)
    cleaned_text:list = clean_body(body,  nlp, for_csv=False)

    # LEXICON AND WORD-EMBEDDING UPDATES
    title_wordIDs, tag_wordIDs, body_wordIDs, body_meaning = handle_words(cleaned_title,cleaned_tags,cleaned_text)


    pos_map = get_position_map(body_wordIDs)

    body_words = [DocumentBodyWord(wordID, positions) for wordID, positions in
                                          pos_map.items()]

    doc = Document(title_wordIDs, tag_wordIDs, body_words)
    wordInDoc_map = _generate_WordInDocMap(title_wordIDs, pos_map)

    return doc, wordInDoc_map, body_meaning

def add_article(url:str):

    A = time.time()
    title, tags, body = _parse_url(url)
    print("Url parsed successfully", time.time() - A)

    if not (valid_body(body) and valid_title(title)):
        raise Exception("INVALID ARTICLE, WILL NOT INDEX")

    A = time.time()
    # LEXICON AND WORD EMBEDDING UPDATES
    doc, wordInDoc_map, body_meaning = _generate_structures(title, tags, body)
    print("Updated lexicon and word embeddings", time.time() - A)

    A = time.time()
    # FORWARD INDEX AND DOCURLDICT UPDATES
    assigned_docID_1 = doc.store(fwd_index)
    assigned_docID_2 = url_dict.store(url)

    # ensure integrity
    assert assigned_docID_1 == assigned_docID_2, "Disparity between fwd index and urldict docID"

    print("Updated Forward index and docurldict", time.time() - A)

    A = time.time()
    # METADATA UPDATE
    assigned_docID = meta.add_doc_metadata(len(doc.title_words), doc.doc_length(), body_meaning)
    assert assigned_docID_1==assigned_docID, "Disparity between metadata assigned docID and actual docID"

    print("Updated metadata", time.time() - A)

    A = time.time()
    # INVERTED INDEX UPDATE
    inv_index.index_document(assigned_docID, doc_wordInDocs=wordInDoc_map)
    print("Updated Inverted Index", time.time() - A)

if __name__ == "__main__":
    try:
        url = "https://medium.com/@eshanuk12/how-to-make-150-a-day-playing-angry-birds-on-mobile-18963359e5cd"
        add_article(url)
    except Exception as e:
        print(e)
        print("Article not Indexed")
        traceback.print_exc()

lexicon.save_lexicon()
