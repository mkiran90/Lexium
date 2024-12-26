import os
import string
import pickle
from src.util.singleton import singleton


#LEXICON NEEDS TO BE CLOSED/SAVED EXPLICITY WHENEVER MODIFIED
@singleton
class Lexicon:

    _LEXICON_PATH = os.path.dirname(os.path.abspath(__file__)) +"/../../res/lexicon/lexicon.pkl"
    _lexicon = {}
    def __init__(self):
        #sync in-memory lexicon up with in-storage lexicon
        if os.path.isfile(self._LEXICON_PATH):
            with open(self._LEXICON_PATH, "rb") as f:
                self._lexicon = pickle.load(f)

    def save_lexicon(self):
        # sync in-storage lexicon with in-memory lexicon
        with open(self._LEXICON_PATH, "wb") as f:
            pickle.dump(self._lexicon, f)

    def size(self):
        return len(self._lexicon)

    def store_word(self, word: string):
        self._lexicon[word] = self.size()

    # wordID, new (boolean)
    def get_or_assign(self, word: string):
        try:
            return self._lexicon[word], False
        except KeyError:

            wordID = self.size()
            self._lexicon[word] = wordID
            return wordID, True

    def get(self, word: string):
        return self._lexicon.get(word)