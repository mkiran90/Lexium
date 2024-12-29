import io
import os
import struct
import threading

from src.util.singleton import singleton
from src.inverted_index.Barrel import Barrel, BarrelFullException
from src.inverted_index.WordPresence import WordPresence, WordInDoc


# SHOULD DO: WORDINDOC should probably have the docID field, its better practice than whatever this is

class InvertedIndexUpdate:
    def __init__(self):
        # -1 represents that its not associated with a specific document
        self.docID = -1
        self.old = {}
        self.new = []

    # sort the old word updates first by barrel_num, then by in_barrel_pos
    def sort(self, inv_index):
        self.old = dict(sorted(self.old.items()))

        for (barrel_num, barrel_updates) in self.old.items():
            self.old[barrel_num] = dict(
                sorted(barrel_updates.items(), key=lambda item: inv_index._get_position(item[0])[1]))

    def to_bytes(self):

        for (i, presence) in enumerate(self.new):
            presence_bytes = presence.encode()
            encoded_bytes = struct.pack("I", presence.wordID) + struct.pack("I", len(presence_bytes)) + presence_bytes
            self.new[i] = encoded_bytes

        for barrel_updates in self.old.values():
            for (wordID, wordInDoc) in barrel_updates.items():
                barrel_updates[wordID] = struct.pack("I", self.docID) + wordInDoc.encode()


@singleton
class InvertedIndex:
    '''
    BARREL_INDEX: first 4 bytes store the RUNNING_BARREL_NUM, then its an array of 5 bytes per wordID (2 bytes barrel_num + 3 bytes in_barrel_pos)
    '''

    _BARREL_INDEX_FILE_PATH = os.path.dirname(os.path.abspath(__file__)) +"/../../res/inverted_index/barrel_index.bin"
    _BARREL_ROOT_PATH = os.path.dirname(os.path.abspath(__file__)) +"/../../res/inverted_index/barrels/"

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
            return None

        barrel = Barrel(barrel_num)
        return barrel.get(in_barrel_pos)

    # novelty checks if word hasnt already been indexed, won't need to do this if check is done externally.
    def index_new_word(self, word_presence, test_novelty, from_bytes=False):

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
            in_barrel_pos = Barrel(barrel_num).index_new_word(word_presence, from_bytes=from_bytes)

        if not from_bytes:
            self._register_word(word_presence.wordID, barrel_num, in_barrel_pos)
        else:
            self._register_word(struct.unpack("I", word_presence[0:4])[0], barrel_num, in_barrel_pos)

    def _get_position_from_file(self, f,wordID):

        offset = 4 + wordID * 5

        f.seek(0, 2) # seek end

        # doesn't yet exist, needs to be added first
        if offset >= f.tell():
            return -1, -1

        f.seek(offset)
        barrel_num = struct.unpack("H", f.read(2))[0]
        in_barrel_pos = int.from_bytes(f.read(3), 'big')
        return barrel_num, in_barrel_pos


    def _distribution(self, index_update, doc_wordInDocs):

        with open(self._BARREL_INDEX_FILE_PATH, "rb") as f:
            for (wordID, wordInDoc) in doc_wordInDocs.items():
                barrel_num, in_barrel_pos = self._get_position_from_file(f,wordID)

                if barrel_num >= 1:

                    if index_update.old.get(barrel_num) is None:
                        index_update.old[barrel_num] = {}

                    index_update.old[barrel_num][wordID] = wordInDoc

                else:
                    presence = WordPresence(wordID)
                    presence.add_doc(index_update.docID, wordInDoc)
                    index_update.new.append(presence)


    def _latch_on(self, j,  presences, barrel_updates, popped_presences):

        for presence in presences:
            wordID = struct.unpack("I", presence[0:4])[0]

            try:
                popped_presences.append(presence + barrel_updates[wordID])
                j -= 1
            except KeyError:
                popped_presences.append(presence)

            return j

    def _barrelwise_accomodation(self, barrel_num, barrel_updates):

        barrel = Barrel(barrel_num)

        popped_presences = []

        req_space = 0

        i = 0
        j = len(barrel_updates)

        # capacity doesn't matter in this case, we must insert anyway
        if barrel.size()==1 and len(barrel_updates) == 1:
            return

        for embedded_bytes in barrel_updates.values():

            if i==j:
                break

            req_space += len(embedded_bytes)
            presences = barrel.truncate(req_space)


            j = self._latch_on(j, presences, barrel_updates, popped_presences)

            i += 1

        return popped_presences, j

    def _accommodation(self, index_update:InvertedIndexUpdate):

        popped_presences = []

        for (barrel_num, barrel_updates) in index_update.old.items():
            presences, valid_update_boundary = self._barrelwise_accomodation(barrel_num, barrel_updates)
            index_update.old[barrel_num] = dict(list(barrel_updates.items())[:valid_update_boundary])
            popped_presences.extend(presences)

        return popped_presences

    def _barrelwise_insertion(self, barrel_num, barrel_updates):

        barrel = Barrel(barrel_num)

        barrel_pos_map = {wordID: self._get_position(wordID)[1] for wordID in barrel_updates}

        # should be guaranteed that the barrel has space for all barrel_updates
        barrel.batch_update(barrel_pos_map, barrel_updates)

    def _insertion(self, index_update):
        threads = []
        for (barrel_num, barrel_updates) in index_update.old.items():
            thread = threading.Thread(target=self._barrelwise_insertion, args=(barrel_num, barrel_updates))
            threads.append(thread)
            thread.start()
        for thread in threads:
            thread.join()


    def index_document(self, docID, doc_wordInDocs: dict[int, WordInDoc]):
        '''
        THE FLOW IS:
        DISTRIBUTION -> SORTING -> BYTE CONVERSION -> ACCOMMODATION -> UPDATE_INSERTION -> NEW_INSERTION
        These are high level subjective operations that must be understood from external documentation.
        '''
        index_update = InvertedIndexUpdate()
        index_update.docID = docID
        self._distribution(index_update, doc_wordInDocs)
        index_update.sort(inv_index=self)
        index_update.to_bytes()
        index_update.new.extend(self._accommodation(index_update))
        self._insertion(index_update)

        # NEW INSERTION, must be sequential
        for presence in index_update.new:
            self.index_new_word(presence, test_novelty=False, from_bytes=True)