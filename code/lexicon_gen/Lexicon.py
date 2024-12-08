import os
import string
import pickle
from code.util.singleton import singleton


#LEXICON NEEDS TO BE CLOSED/SAVED EXPLICITY WHENEVER MODIFIED
@singleton
class Lexicon:

    LEXICON_PATH = "../../res/lexicon/lexicon.pkl"
    lexicon = {}
    def __init__(self):
        #sync in-memory lexicon up with in-storage lexicon
        if os.path.isfile(self.LEXICON_PATH):
            with open(self.LEXICON_PATH, "rb") as f:
                self.lexicon = pickle.load(f)

    def save_lexicon(self):
        # sync in-storage lexicon with in-memory lexicon
        with open(self.LEXICON_PATH, "wb") as f:
            pickle.dump(self.lexicon, f)

    def size(self):
        return len(self.lexicon)

    def store_word(self, word: string):
        self.lexicon[word] = self.size()

    #returns wordID if word is in lexicon, else store word and return the newly assigned wordID
    def get_or_assign(self, word: string):
        try:
            return self.lexicon[word]
        except KeyError:

            wordID = self.size()
            self.lexicon[word] = wordID
            return wordID
