import io
import os
import struct

from src.util.singleton import singleton
from src.inverted_index.Barrel import Barrel, BarrelFullException
from src.inverted_index.WordPresence import WordPresence


@singleton
class InvertedIndex:
    '''
    BARREL_INDEX: first 4 bytes store the RUNNING_BARREL_NUM, then its an array of 5 bytes per wordID (2 bytes barrel_num + 3 bytes in_barrel_pos)
    '''

    _BARREL_INDEX_FILE_PATH = "../../res/inverted_index/barrel_index.bin"
    _BARREL_ROOT_PATH = "../../res/inverted_index/barrels/"

    def __init__(self):

        if not os.path.isfile(self._BARREL_INDEX_FILE_PATH):
            self._init_index_file()

        os.makedirs(self._BARREL_ROOT_PATH, exist_ok=True)

    def _running_barrel_num(self):
        with open(self._BARREL_INDEX_FILE_PATH, "rb") as f:
            return struct.unpack("I", f.read(4))[0]

    def _init_index_file(self):

        from src.lexicon_gen.Lexicon import Lexicon
        with open(self._BARREL_INDEX_FILE_PATH, "wb") as f:
            f.write(struct.pack("I", 1))  # first 4 bytes tell CURRENT_BARREL_NUM
            lexicon = Lexicon()
            size = lexicon.size()
            del lexicon
            bytes = struct.pack('H', 0) + (0).to_bytes(3, byteorder='big')
            f.write(bytes * size)  # initial state, all wordIDs are "not indexed" (0,0) position.

    # a return of 0,0 means the document is NOT YET INDEXED but is in lexicon
    # a return of -1,1 means its not in lexicon and obviously not indexed
    def _get_position(self, wordID):

        offset = 4 + wordID * 5

        with open(self._BARREL_INDEX_FILE_PATH, "a+b") as f:
            # doesn't yet exist, needs to be added first
            if offset >= f.tell():
                return -1, -1

            f.seek(offset)
            barrel_num = struct.unpack("H", f.read(2))[0]
            in_barrel_pos = int.from_bytes(f.read(3), 'big')
            return barrel_num, in_barrel_pos

    # this creates/updates an entry in the barrel_index file
    def _register_word(self, wordID, barrel_num, in_barrel_pos):
        offset = 4 + wordID * 5

        with open(self._BARREL_INDEX_FILE_PATH, "r+b") as f:
            # move to end
            f.seek(0, io.SEEK_END)
            '''
            this happens in the following scenario:
            wordID exceeds the last stored wordID in barrel index, but the existence of such a wordID implies that wordIDs smaller than it also
            exist in the lexicon since its sequential, so pre-register them as 0,0
            '''
            empty_bytes = offset - f.tell()
            if empty_bytes > 0:
                f.write(struct.pack('B', 0) * empty_bytes)

            f.seek(offset)
            f.write(struct.pack("H", barrel_num))
            f.write(in_barrel_pos.to_bytes(3, 'big'))

    def _increment_running_barrel(self):
        with open(self._BARREL_INDEX_FILE_PATH, "r+b") as f:
            old = struct.unpack("I", f.read(4))[0]
            f.seek(0)
            f.write(struct.pack("I", old + 1))

    def get(self, wordID):
        barrel_num, in_barrel_pos = self._get_position(wordID)

        if barrel_num < 1:  # 0 and -1 both invalid
            return

        barrel = Barrel(barrel_num)
        return barrel.get(in_barrel_pos)


    def _accomodate(self, barrel, num_bytes):
        popped_words = barrel.truncate(num_bytes)
        for word_bytes in popped_words:
            self.index_new_word(word_presence=word_bytes, test_novelty=False, from_bytes=True)

    # this is the more general operation and will be used when a new document has to be stored in inverted index
    # document will be split into a set of (wordID,wordInDoc) pairs, each being added.
    # from_bytes should only be true if wordInDoc represents the COMPLETE bytes |docID|wordInDoc|
    def add(self, wordID, docID, wordInDoc, from_bytes = False):

        barrel_num, in_barrel_pos = self._get_position(wordID)
        if not from_bytes:
            encoded_bytes = struct.pack("I", docID) + wordInDoc.encode()
        else:
            encoded_bytes = wordInDoc

        # updating the word, it is already indexed
        if barrel_num >= 1:
            barrel = Barrel(barrel_num)
            try:
                barrel.update_word_presence(in_barrel_pos, docID, encoded_bytes, from_bytes=True)
            except BarrelFullException:
                   self._accomodate(barrel, len(encoded_bytes))
                   self.add(wordID, docID, encoded_bytes, from_bytes=True)


        # barrel_num = 0 or -1
        else:
            presence = WordPresence(wordID)
            presence.add_doc(docID, wordInDoc)

            # this registers as well
            self.index_new_word(presence, test_novelty=False)

    # novely checks if word hasnt already been indexed, won't need to do this if check is done externally.
    def index_new_word(self, word_presence, test_novelty, from_bytes = False):

        if test_novelty:
            barrel_num, _ = self._get_position(word_presence.wordID)

            # i.e not yet indexed
            assert barrel_num < 1

        barrel_num = self._running_barrel_num()

        barrel = Barrel(barrel_num)


        try:
            in_barrel_pos = barrel.index_new_word(word_presence, from_bytes=from_bytes)
        except BarrelFullException:
            barrel_num += 1
            self._increment_running_barrel()
            in_barrel_pos = Barrel(barrel_num).index_new_word(word_presence,from_bytes=from_bytes)

        if not from_bytes:
            self._register_word(word_presence.wordID, barrel_num, in_barrel_pos)
        else:
            self._register_word(struct.unpack("I", word_presence[0:4])[0], barrel_num, in_barrel_pos)