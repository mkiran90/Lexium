import os
import string
import struct
from util.singleton import singleton

@singleton
class Lexicon:

    LEXICON_ROOT = "../../res/lexicon"
    SIZE_FILE = LEXICON_ROOT + "size.bin"
    def __init__(self):

        # ensure lexicon directory exists.
        os.makedirs(self.LEXICON_ROOT, exist_ok=True)

        # ensure size file exists
        if not os.path.isfile(self.SIZE_FILE):
            with open(self.SIZE_FILE, "wb") as size_file:
                size_file.write(b'\x00\x00\x00\x00') # write 0 as uint32

    def size(self):
        with open(self.SIZE_FILE, "rb") as fwd_index:
            return struct.unpack("I", fwd_index.read(4))[0]


    def get_directory(self, word:string):
        return self.LEXICON_ROOT + "/".join(str(ord(char)) for char in word) + "/"

    def store_word(self, word: string):

        directory = self.get_directory(word)
        os.makedirs(directory, exist_ok=True) # make directory to store data file in
        file_path = directory + "data.bin"

        wordID = self.size()

        with open(file_path, 'wb') as file:
            file.write(struct.pack('I', wordID))

    # returns wordID or None (if it doesn't exist in lexicon)
    def get_wordID(self, word: string):
        directory_path = self.get_directory(word)
        file_path = directory_path + "data.bin"

        try:
            with open(file_path, 'rb') as file:
                return struct.unpack("I", file.read(4))[0]
        except FileNotFoundError:
            return None

    # returns wordID if word is in lexicon, else store word and return the newly assigned wordID
    def get_with_store(self, word):
        directory = self.get_directory(word)
        os.makedirs(directory, exist_ok=True)
        file_path = directory + "data.bin"

        # file exists
        if os.path.isfile(file_path):
            with open(file_path, 'rb') as file:
                wordID = struct.unpack("I", file.read(4))[0]
        else:
            wordID = self.size()
            with open(file_path, 'wb') as file:
                file.write(struct.pack('I', wordID))
        return wordID


