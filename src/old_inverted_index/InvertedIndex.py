import math
import os
import pickle

from src.util.singleton import singleton
@singleton
class InvertedIndex:

    BARREL_ROOT_PATH = "../../res/inverted_index/"

    BARREL_CAPACITY = 1000

    open_barrels = {}

    def __init__(self):
        os.makedirs(self.BARREL_ROOT_PATH, exist_ok=True)

    def get_barrel_path(self, barrel_num):
        return self.BARREL_ROOT_PATH + f"barrel_{barrel_num}.pkl"

    # if it exists, returns the barrel (loads it if it isnt open)
    # if it doesn't return None
    def load_barrel(self, barrel_num) -> dict:

        barrel = self.open_barrels.get(barrel_num)
        if barrel is None:
            try:
                with open(self.get_barrel_path(barrel_num), "rb") as f:
                    barrel =  pickle.load(f)
                self.open_barrels[barrel_num] = barrel
            except FileNotFoundError:
                pass # if file doesn't exist, barrel remains None.

        return barrel

    def close_and_save_barrel(self, barrel_num):

        barrel = self.open_barrels.get(barrel_num)

        if barrel is not None:
            with open(self.get_barrel_path(barrel_num), "wb") as f:
                pickle.dump(barrel, f)
            del self.open_barrels[barrel_num]

    def wordID_to_barrelNum(self, wordID):
        return math.floor(wordID/self.BARREL_CAPACITY)

    # keeps the barrel open after a fetch, returns doclist, or None if wordID not indexed.
    def get(self, wordID):
        barrel_num = self.wordID_to_barrelNum(wordID)
        barrel = self.load_barrel(barrel_num)

        if barrel is None:
            return None

        return barrel[wordID]

    # closes the barrel after fetching, returns doclist, None if wordID not indexed
    def get_and_close(self, wordID):
        barrel_num = self.wordID_to_barrelNum(wordID)
        barrel = self.load_barrel(barrel_num)

        if barrel is None:
            return None

        doclist = barrel[wordID]
        self.close_and_save_barrel(barrel_num)
        return doclist

    def make_barrel(self, barrel_num):
        barrel = {}
        self.open_barrels[barrel_num] = barrel
        return barrel
    def put(self, wordID, docID):
        barrel_num = self.wordID_to_barrelNum(wordID)
        barrel = self.load_barrel(barrel_num)

        # barrel doesn't exist
        if barrel is None:
            barrel = self.make_barrel(barrel_num)
            barrel[wordID] = {docID}
        else:
            # wordID doesnt exist in barrel, not yet indexed
            if barrel.get(wordID) is None:
                barrel[wordID] = {docID}
            # there already exists a barrel
            else:
                barrel[wordID].add(docID)

    # close all barrels in the index, save "State" of inverted index
    def close(self):
        for (barrel_num, barrel) in self.open_barrels.items():
            with open(self.get_barrel_path(barrel_num), "wb") as f:
                pickle.dump(barrel, f)
        self.open_barrels = {}

