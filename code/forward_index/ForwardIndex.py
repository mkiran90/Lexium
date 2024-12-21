import struct
import os

from code.util.singleton import singleton
import random
'''
Structure of Forward Index Data File
first 4 bytes are num_documents, unsigned integer32.
afterwards begins a list of encoded Documents

For each Document:
the format is: |num_bytes|num_title_words|title_words|num_tags|tags|num_body_words|DocumentBodyWords|
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
    _OFFSET_FILE_PATH = "../../res/forward_index/offset_file.bin"
    _DATA_FILE_PATH = "../../res/forward_index/data_file.bin"

    def __init__(self):
        if not os.path.isfile(self._DATA_FILE_PATH):
            self._create_data_file()
        if not os.path.isfile(self._OFFSET_FILE_PATH):
            open(self._OFFSET_FILE_PATH, "x") # safe creation

    @classmethod
    def _create_data_file(cls):
        # first 4 bytes need to be occupied by the size of the forward index, which rn is 0.
        with open(cls._DATA_FILE_PATH, "wb") as data_file:
            data_file.write(b'\x00\x00\x00\x00') # binary of 0 as uint32

    def size(self):
        with open(self._DATA_FILE_PATH, "rb") as fwd_index:
            return struct.unpack("I", fwd_index.read(4))[0]


    # get pointer (offset for fwd index data file) to first byte of data for this docID
    def _get_offset(self, docID: int):
        with open(self._OFFSET_FILE_PATH, "rb") as offset_file:
            offset_file.seek(4 * docID)
            return struct.unpack("I", offset_file.read(4))[0]

    def get(self, docID: int):
        from code.document.Document import Document

        offset: int = self._get_offset(docID)

        with open(self._DATA_FILE_PATH, "rb") as fwd_index:
            fwd_index.seek(offset)

            # first 4 bytes give number of bytes that encode entire document
            num_bytes = struct.unpack("I", fwd_index.read(4))[0]

            docbytes = fwd_index.read(num_bytes)

            return Document.decode(docbytes)

    def get_document_lite(self, docID: int):
        from code.document.DocumentLite import DocumentLite

        offset: int = self._get_offset(docID)

        with open(self._DATA_FILE_PATH, "rb") as fwd_index:
            fwd_index.seek(offset)

            # first 4 bytes give number of bytes that encode entire document
            num_bytes = struct.unpack("I", fwd_index.read(4))[0]

            docbytes = fwd_index.read(num_bytes)

            return DocumentLite.decode(docbytes)


