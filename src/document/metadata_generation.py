from gensim.models import KeyedVectors

from src.document.DocumentMetadata import MetaIndex
from src.lexicon_gen.Lexicon import Lexicon
from src.forward_index.ForwardIndex import ForwardIndex

meta = MetaIndex()
lexicon = Lexicon()
inv_lexicon = list(lexicon._lexicon.keys())
model = KeyedVectors.load_word2vec_format("../../res/GoogleNews-vectors-negative300.bin", binary=True)
fwd_index = ForwardIndex()


def generation():
    for docID in range(fwd_index.size()):
        doc = fwd_index.get(docID)
        assignedDocID = meta.add_document(doc, model, inv_lexicon)
        assert docID == assignedDocID, f"{assignedDocID}, {docID}"

def verification():
    for docID in range(fwd_index.size()):
        doc = fwd_index.get(docID)
        body_len = meta.get_doc_length(docID)
        title_len = meta.get_title_length(docID)
        assert title_len == len(doc.title_words) and doc.doc_length() == body_len


if __name__ == "__main__":
    # generation()
    verification()
