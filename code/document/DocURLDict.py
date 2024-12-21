import os.path
import struct

from code.util.singleton import singleton

@singleton
class DocURLDict:
    _DATA_FILE_PATH = "../../res/doc_url_dict/doc_url_dict_data.txt"
    _OFFSET_FILE_PATH = "../../res/doc_url_dict/doc_url_dict_offset.bin"

    def __init__(self):
        if not os.path.isfile(self._DATA_FILE_PATH):
            open(self._DATA_FILE_PATH, "w")
        if not os.path.isfile(self._OFFSET_FILE_PATH):
            open(self._OFFSET_FILE_PATH, "wb")
    def _get_offset(self, docID: int):
        with open(self._OFFSET_FILE_PATH, "rb") as offset_file:
            offset_file.seek(4 * docID)
            return struct.unpack("I", offset_file.read(4))[0]

    def get(self, docID:int):
        offset:int = self._get_offset(docID)
        with open(self._DATA_FILE_PATH, "r", encoding="utf-8") as data_file:
            data_file.seek(offset)
            url:str = data_file.readline()
            return url.rstrip()

    def store(self, url:str):
        with open(self._DATA_FILE_PATH, "a", encoding="utf-8") as data_file:
            offset = data_file.tell()
            data_file.write(url + "\n") # write the URL as one line

        with open(self._OFFSET_FILE_PATH, "ab") as offset_file:
            docID = int(offset_file.tell()/4)
            offset_file.write(struct.pack("I", offset))  # offset will be stored as uint32
            return docID

    def size(self):
        with open(self._OFFSET_FILE_PATH, "ab") as offset_file:
            size = offset_file.tell()/4
        return size


