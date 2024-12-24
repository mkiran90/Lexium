import os
import struct

import numpy as np

class WordEmbedding:

    _EMBEDDINGS_FILE_PATH = "../../res/lexicon/embeddings_file.bin"


    def __init__(self):
        if not os.path.isfile(self._EMBEDDINGS_FILE_PATH):
            with open(self._EMBEDDINGS_FILE_PATH, "wb") as embeddings_file:
                pass

    def add_word_embedding(self, wordID,  word_embedding: np.ndarray):

        offset = 1200*wordID

        with open(self._EMBEDDINGS_FILE_PATH, "r+b") as f:

            # go to end
            f.seek(0, 2)

            end_pos = f.tell()

            # fill in the gaps
            if offset > end_pos:
                f.write(struct.pack("B",0)*(offset - end_pos))

            assert f.tell() == offset, "Disparity between wordID and corresponding offset"

            f.write(word_embedding.tobytes())



    def get_word_embedding(self, word_id: int):
        offset = 1200 * word_id

        with open(self._EMBEDDINGS_FILE_PATH, "rb") as embeddings_file:
            embeddings_file.seek(offset)

            embedding_vector = np.frombuffer(embeddings_file.read(1200), dtype=np.float32)

        return embedding_vector


