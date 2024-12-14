import struct
import os
from code.util.singleton import singleton
import random
'''
Structure of Forward Index Data File
first 4 bytes are num_documents, unsigned integer32.
afterwards begins a list of encoded Documents

For each Document:
the format is: |num_title_words|title_words|num_tags|tags|num_body_words|DocumentBodyWords|
num_title_words -> 1b uint8
title_words -> num_title_words * 4 b (4b wordIDs uint32)
num_tags -> 1b uint8
tags -> num_tags * 4 b (4b wordIDs uint32)
num_body_words -> 4b uint32 
For each DocumentBodyWord:
|wordID|num_positions|positions|
wordID -> 4b uint32
num_positions -> 2b uint16
positions -> num_positions * 4 b (4b wordIDs uint32)
'''


@singleton
class ForwardIndex:
    OFFSET_FILE_PATH = "../../res/forward_index/offset_file.bin"
    DATA_FILE_PATH = "../../res/forward_index/data_file.bin"

    def __init__(self):
        if not os.path.isfile(self.DATA_FILE_PATH):
            self.create_data_file()
        if not os.path.isfile(self.OFFSET_FILE_PATH):
            open(self.OFFSET_FILE_PATH, "x") # safe creation

    @classmethod
    def create_data_file(cls):
        # first 4 bytes need to be occupied by the size of the forward index, which rn is 0.
        with open(cls.DATA_FILE_PATH, "wb") as data_file:
            data_file.write(b'\x00\x00\x00\x00') # binary of 0 as uint32

    def size(self):
        with open(self.DATA_FILE_PATH, "rb") as fwd_index:
            return struct.unpack("I", fwd_index.read(4))[0]

    def dummy_populate(self, num_doc):
        from code.document.Document import Document, DocumentBodyWord
        for _ in range(num_doc):
            dummyDocument = Document(0, [1] * 10, [1] * 5,
                                     [DocumentBodyWord(1, [1] * random.randint(1, 10))] * random.randint(100, 300))
            dummyDocument.store()

    # get pointer (offset for fwd index data file) to first byte of data for this docID
    def get_offset(self, docID: int):
        with open(self.OFFSET_FILE_PATH, "rb") as offset_file:
            offset_file.seek(4 * docID)
            return struct.unpack("I", offset_file.read(4))[0]


    def get_document(self, docID: int):
        from code.document.Document import Document, DocumentBodyWord

        offset: int = self.get_offset(docID)

        with open(self.DATA_FILE_PATH, "rb") as fwd_index:
            fwd_index.seek(offset)

            # Read and decode the number of title words
            num_title_words = struct.unpack("B", fwd_index.read(1))[0]  # read 1 byte, decode as uint8

            # Read all title word data (4 bytes for each word, decode as uint32)
            title_words_data = fwd_index.read(num_title_words * 4)
            title_words = list(struct.unpack(f"{num_title_words}I", title_words_data))

            # Read and decode the number of tags
            num_tags = struct.unpack("B", fwd_index.read(1))[0]  # read 1 byte, decode as uint8

            # Read all tag data (4 bytes for each tag, decode as uint32)
            tags_data = fwd_index.read(num_tags * 4)
            tags = list(struct.unpack(f"{num_tags}I", tags_data))

            # read DocumentBodyWords
            body_words: list[DocumentBodyWord] = []
            num_body_words = struct.unpack("I", fwd_index.read(4))[0]
            for _ in range(num_body_words):
                wordID = struct.unpack("I", fwd_index.read(4))[0]
                num_positions = struct.unpack("H", fwd_index.read(2))[0]  # 2 byte uint16
                positions = list(struct.unpack(f"{num_positions}I", fwd_index.read(4 * num_positions)))

                body_words.append(DocumentBodyWord(wordID, positions))

        return Document(title_words, tags, body_words)