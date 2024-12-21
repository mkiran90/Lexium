from code.forward_index.ForwardIndex import ForwardIndex
from InvertedIndex import InvertedIndex
from code.lexicon_gen.Lexicon import Lexicon
from code.document.DocURLDict import DocURLDict

fwd_index = ForwardIndex()
inv_index = InvertedIndex()
# takes about 127 seconds
def build_inv_index():
    for docID in range(0, fwd_index.size()):
        doc = fwd_index.get(docID)
        for word in doc.body_words:
            inv_index.put(word.wordID, docID)
        for wordID in doc.title_words:
            inv_index.put(wordID, docID)
        print(docID)

if __name__ == "__main__":
    #build_inv_index()
    pass
inv_index.close()