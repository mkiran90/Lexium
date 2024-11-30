import os.path
import struct
import sys

from ..util.singleton import singleton

@singleton
class DocURLDict:
    DATA_FILE_PATH = "../../res/doc_url_dict/doc_url_dict_data.bin"
    OFFSET_FILE_PATH = "../../res/doc_url_dict/doc_url_dict_offset.bin"

    def __init__(self):
        if not os.path.isfile(self.DATA_FILE_PATH):
            open(self.DATA_FILE_PATH, "wb")
        if not os.path.isfile(self.OFFSET_FILE_PATH):
            open(self.OFFSET_FILE_PATH, "wb")
    def get_offset(self, docID: int):
        with open(self.OFFSET_FILE_PATH, "rb") as offset_file:
            offset_file.seek(4 * docID)
            return struct.unpack("I", offset_file.read(4))[0]

    def get_url(self, docID:int):
        offset:int = self.get_offset(docID)
        with open(self.DATA_FILE_PATH, "rb") as data_file:

            data_file.seek(offset)
            num_char = struct.unpack("H", data_file.read(2))[0]
            url:str = data_file.read(num_char).decode("ascii")
            return url

    def store_url(self, url:str):
        with open(self.DATA_FILE_PATH, "ab") as data_file:
            offset = data_file.tell()
            data_file.write(struct.pack("H", len(url))) # store the length as uint16
            data_file.write(url.encode("ascii")) # each character will be one byte

        with open(self.OFFSET_FILE_PATH, "ab") as offset_file:
            docID = offset_file.tell()/4
            offset_file.write(struct.pack("I", offset))  # offset will be stored as uint32
            return docID

    def size(self):
        with open(self.OFFSET_FILE_PATH, "ab") as offset_file:
            size = offset_file.tell()/4
        return size

print(sys.path)