import os
import struct

import numpy as np
from code.util.singleton import singleton

@singleton
class DocumentMetadata:
    _METADATA_FILE_PATH = "../../res/doc_metadata/metadata_file.bin"



    def __init__(self):
        if not os.path.isfile(self._METADATA_FILE_PATH):
            self._create_data_file()

    @classmethod
    def _create_data_file(cls):
        with open(cls._METADATA_FILE_PATH, "wb") as metadata_file:
            metadata_file.write(b'\x00\x00\x00\x00')

    def total_word_count(self):
        with open(self._METADATA_FILE_PATH, "rb") as metadata_file:
            return struct.unpack("I", metadata_file.read(4))[0]

    def get_doc_length(self, doc_id: int):

        offset = 4 + (doc_id * 1204)

        with open(self._METADATA_FILE_PATH, "rb") as metadata_file:
            metadata_file.seek(offset)

            doc_length = struct.unpack("I", metadata_file.read(4))[0]

        return doc_length

    def get_doc_embedding(self, doc_id: int):
        # Calculate the offset based on the doc_id
        offset = 8 + (doc_id * 1204)

        with open(self._METADATA_FILE_PATH, "rb") as metadata_file:

            metadata_file.seek(offset)

            embedding_vector = np.frombuffer(metadata_file.read(1200), dtype=np.float32)

        return embedding_vector

    def add_doc_metadata(self, doc_length: int, embedding_vector: np.ndarray):

        if not isinstance(embedding_vector, np.ndarray):
            raise ValueError("embedding_vector must be a numpy array")

        if embedding_vector.shape != (300,):
            raise ValueError("embedding_vector must have a shape of (300,)")

        with open(self._METADATA_FILE_PATH, "r+b") as metadata_file:

            total_corpus = struct.unpack("I", metadata_file.read(4))[0]
            total_corpus += doc_length

            metadata_file.seek(0)
            metadata_file.write(struct.pack("I", total_corpus))


            metadata_file.seek(0, 2)

            metadata_file.write(struct.pack("I", doc_length))
            metadata_file.write(embedding_vector.tobytes())


    def get_word_vector(self, word, model):
        """
        Gets the word vector for a given word.
        :param word: Input word.
        :param model: Pre-trained word vector model.
        :return: Word vector (list) or None if the word is not in the vocabulary.
        """
        if word in model.key_to_index:
            return model[word]
        else:
            return None

    def body_meaning(self, body_words, model, inv_lexicon):

        total = 0
        vec_sum = np.zeros(shape=(300,))
        for word in body_words:
            token = inv_lexicon[word.wordID]
            vec = self.get_word_vector(token, model)
            if vec is None:
                continue
            summed_vec = vec * word.frequency()
            vec_sum += summed_vec
            total += word.frequency()

        return (vec_sum / total).astype(np.float32)




