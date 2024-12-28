import os
import struct
import time

import numpy as np
from src.util.singleton import singleton
from src.util.util_functions import body_meaning

"""
The structure is:
|corpus_length|meta|meta|meta|...
each |meta| is |title_len|body_len|word_embedding|
corpus_len -> uint32
title_len -> uint8
body_len -> uint16
word_embedding -> 1200 bytes
"""

print("cwd in meta: ", os.getcwd())

class DocumentRankingMeta:
    def __init__(self, title_length, body_length, meaning):
        self.meaning = meaning
        self.body_length = body_length
        self.title_length = title_length



@singleton
class RankingMetaIndex:
    _METADATA_FILE_PATH =  os.path.dirname(os.path.abspath(__file__)) + "/../../res/metadata/ranking/data.bin"

    def __init__(self):
        if not os.path.isfile(self._METADATA_FILE_PATH):
            self._create_data_file()

    @classmethod
    def _create_data_file(cls):
        with open(cls._METADATA_FILE_PATH, "wb") as metadata_file:
            metadata_file.write(b'\x00\x00\x00\x00')

    @classmethod
    def _get_offset(cls, docID):
        return 4 + (docID * 1203)

    def total_word_count(self):
        with open(self._METADATA_FILE_PATH, "rb") as metadata_file:
            return struct.unpack("I", metadata_file.read(4))[0]

    def get_doc_length(self, doc_id: int):

        offset = self._get_offset(doc_id)

        with open(self._METADATA_FILE_PATH, "rb") as metadata_file:
            metadata_file.seek(offset + 1) # skip the title_len

            doc_length = struct.unpack("H", metadata_file.read(2))[0]

        return doc_length

    def get_title_length(self, doc_id: int):

        offset = self._get_offset(doc_id)

        with open(self._METADATA_FILE_PATH, "rb") as metadata_file:
            metadata_file.seek(offset)

            return struct.unpack("B", metadata_file.read(1))[0]


    def get_doc_embedding(self, doc_id: int):

        offset = self._get_offset(doc_id)

        with open(self._METADATA_FILE_PATH, "rb") as metadata_file:

            metadata_file.seek(offset + 3) # skip the doc_len and title_len

            embedding_vector = np.frombuffer(metadata_file.read(1200), dtype=np.float32)

        return embedding_vector

    def add_doc_metadata(self, title_len, doc_length: int, embedding_vector: np.ndarray):

        with open(self._METADATA_FILE_PATH, "r+b") as metadata_file:

            total_corpus = struct.unpack("I", metadata_file.read(4))[0]
            total_corpus += doc_length

            metadata_file.seek(0)
            metadata_file.write(struct.pack("I", total_corpus))

            metadata_file.seek(0, 2)

            offset = metadata_file.tell()

            metadata_file.write(struct.pack("B", title_len))
            metadata_file.write(struct.pack("H", doc_length))
            metadata_file.write(embedding_vector.tobytes())

            # return the docID needed to access the added document
            return (offset - 4)//1203
    def add_document(self, doc, model, inv_lexicon):
        title_len = len(doc.title_words)
        doc_len = doc.doc_length()
        meaning_vec = body_meaning(doc.body_words, model, inv_lexicon)
        return self.add_doc_metadata(title_len, doc_len, meaning_vec)

    def batch_load(self, doc_list):

        doc_map = {}

        with open(self._METADATA_FILE_PATH, "rb") as f:
            for docID in doc_list:
                f.seek(self._get_offset(docID))
                doc_bytes = f.read(1203)
                doc_map[docID] = DocumentRankingMeta(title_length=struct.unpack("B", doc_bytes[0:1])[0], body_length=struct.unpack("H", doc_bytes[1:3])[0], meaning=np.frombuffer(doc_bytes[3:], dtype=np.float32))

        return doc_map


if __name__ == "__main__":

    meta = RankingMetaIndex()
    doc_list = list(range(100000))
    A = time.time()
    meta.batch_load(doc_list)
    print(time.time() - A)


