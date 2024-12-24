import pickle

from src.forward_index.ForwardIndex import ForwardIndex
from src.inverted_index.InvertedIndex import InvertedIndex
from src.lexicon_gen.Lexicon import Lexicon
from src.inverted_index.WordPresence import WordPresence,WordInDoc
fwd_index = ForwardIndex()
inv_index = InvertedIndex()
lexicon = Lexicon()

def convertToWordInDocMap(doc):
    wordInDoc_map = {}
    for (wordID, body_positions) in doc.body_words.items():
         wordInDoc_map[wordID] = WordInDoc([], body_positions)
    for (i,wordID) in enumerate(doc.title_words):

        try:
            wordInDoc_map[wordID].title_positions.append(i)
        except KeyError:
            wordInDoc_map[wordID] = WordInDoc([i],[])

    return wordInDoc_map


# this is inclusive
def store_presence(i,startWordID, endWordID):
    presenceMap = {}
    for wordID in range(startWordID, endWordID + 1):
        presenceMap[wordID] = WordPresence(wordID)
    for docID in range(fwd_index.size()):
        doc = fwd_index.get_document_lite(docID)
        wordInDoc_map = convertToWordInDocMap(doc)
        del doc
        for (wordID, wordInDoc) in wordInDoc_map.items():
            if startWordID <= wordID <= endWordID:
                presenceMap[wordID].add_doc(docID, wordInDoc)
        del wordInDoc_map
        print(docID)
    path = f"../../res/WordPresenceMaps/presenceMap{i}.pkl"
    with open(path, "wb") as f:
        pickle.dump(presenceMap, f)

def build_word_presences():

    # these ranges take into account the disproportionate sizes of the wordPresences
    ranges = [(0,500),(501,1500),(1501, 3000),(3001,6000),(6001, 12000),(12001, 30000),(30_001, 100_000),[100_001, lexicon.size()-1]]

    for (i, interval) in enumerate(ranges):
        store_presence(i, interval[0], interval[1])


def index_word_presences():

    root_path = "../../res/WordPresenceMaps/"
    for i in range(8):
        path = root_path + f"presenceMap{i}.pkl"
        with open(path, "rb") as f:
            presence_map = pickle.load(f)
        for presence in presence_map.values():
            inv_index.index_new_word(presence, test_novelty=True)
        del presence_map
        print(i)





if __name__ == "__main__":

    generate = False
    if generate:
        build_word_presences()
        index_word_presences()