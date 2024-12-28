from src.meta.RankingMetaIndex import RankingMetaIndex
from src.lexicon_gen.Lexicon import Lexicon
from src.forward_index.ForwardIndex import ForwardIndex
from src.util.util_functions import get_word2vec

meta = RankingMetaIndex()
lexicon = Lexicon()
inv_lexicon = list(lexicon._lexicon.keys())
model = get_word2vec()
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
