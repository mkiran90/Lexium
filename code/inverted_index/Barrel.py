import io
import os
import struct
import tempfile

from code.inverted_index.WordPresence import WordPresence

class BarrelFullException(Exception):
    pass

class Barrel:
    BARREL_CAPACITY = 1024*1024 * 1024  # 1GB
    PARENT_PATH = "../../res/inverted_index/barrels/"

    def __init__(self, barrel_num):

        self.BARREL_PATH = f"{self.PARENT_PATH}{barrel_num}/"
        os.makedirs(self.BARREL_PATH, exist_ok=True)

        self.DATA_FILE_PATH = self.BARREL_PATH + "data.bin"
        self.OFFSET_FILE_PATH = self.BARREL_PATH + "offsets.bin"

        if not os.path.isfile(self.DATA_FILE_PATH):
            open(self.DATA_FILE_PATH, "wb")
        if not os.path.isfile(self.OFFSET_FILE_PATH):
            open(self.OFFSET_FILE_PATH, "wb")

    def has_space(self, num_bytes):
        with open(self.DATA_FILE_PATH, "ab") as f:
            return (self.BARREL_CAPACITY - f.tell()) >= num_bytes

    # number of indexed words
    def size(self):
        with open(self.OFFSET_FILE_PATH, "ab") as f:
            return f.tell() / 4

    def size_bytes(self):
        with open(self.DATA_FILE_PATH, "ab") as f:
            return f.tell()

    def _get_offset(self, in_barrel_pos):
        with open(self.OFFSET_FILE_PATH, "rb") as f:
            f.seek(4*in_barrel_pos)
            return struct.unpack('I', f.read(4))[0]

    def get(self, in_barrel_pos):
        offset = self._get_offset(in_barrel_pos)
        with open(self.DATA_FILE_PATH, "rb") as f:
            f.seek(offset)
            wordID = struct.unpack('I', f.read(4))[0]
            num_bytes = struct.unpack('I', f.read(4))[0]
            encoded_bytes = f.read(num_bytes)
            return WordPresence.decode(wordID, encoded_bytes)


    # 256 kB chunk size
    def _insert(self,f, position, new_bytes, chunk_size=256 * 1024):

        # Ensure the file descriptor is at the beginning
        f.seek(0)

        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file_path = temp_file.name

            # Write content up to the insertion point
            f.seek(0)
            temp_file.write(f.read(position))

            # Write the new data
            temp_file.write(new_bytes)

            # Write the remaining content in chunks
            while chunk := f.read(chunk_size):
                temp_file.write(chunk)

        # Replace the original file content
        f.seek(0)  # Reset file descriptor to the beginning
        with open(temp_file_path, 'rb') as temp_file:
            f.write(temp_file.read())

        # Truncate the file in case it becomes shorter
        f.truncate()

        # Clean up the temporary file
        os.remove(temp_file_path)

    # increment all offsets that come after in_barrel_pos in offset file by num_bytes
    def _increment_offsets(self, in_barrel_pos, num_bytes):
        with open(self.OFFSET_FILE_PATH, "r+b") as f:
             offset = 4*(in_barrel_pos + 1) # start from position AFTER in_barrel_pos
             f.seek(offset)
             offset_bytes = f.read()
             num_offsets = len(offset_bytes)//4
             offsets = struct.unpack(f"{num_offsets}I", offset_bytes)
             updated_offsets = [x + num_bytes for x in offsets]
             del offsets
             del offset_bytes
             f.seek(offset)
             f.write(struct.pack(f"{num_offsets}I", *updated_offsets))

    # from_bytes should only be TRUE if word_presence represents ALL BYTES of the entry i.e |docID|wordInDoc|
    def update_word_presence(self, in_barrel_pos, docID, wordInDoc, from_bytes = False):
        if from_bytes:
            encoded_bytes = wordInDoc
        else:
            encoded_bytes = struct.pack("I", docID) + wordInDoc.encode()

        if not self.has_space(len(encoded_bytes)):
            raise BarrelFullException

        offset = self._get_offset(in_barrel_pos)

        with open(self.DATA_FILE_PATH, "r+b") as f:
            f.seek(offset+4) # first 4 bytes are wordID, so skip
            num_bytes = struct.unpack("I", f.read(4))[0]
            num_docInWords = struct.unpack("I", f.read(4))[0]
            self._insert(f, offset + 8 + num_bytes, encoded_bytes)

            # update byte size of wordPresence
            f.seek(offset+4)
            f.write(struct.pack("I", num_bytes + len(encoded_bytes)))

            # update num_docInWords
            f.seek(offset + 8)
            f.write(struct.pack("I", num_docInWords + 1))

            self._increment_offsets(in_barrel_pos, len(encoded_bytes))

    # this is only relevant when directly adding entire word presences when building inv index from fwd index
    # is is guaranteed by caller that the wordID is not indexed i.e in barrel index get_position(wordID) should return 0,0 / -1,-1
    # from_bytes should only be TRUE if word_presence represents ALL BYTES of the entry i.e |wordID|num_bytes|presence|
    def index_new_word(self, word_presence, from_bytes = False):

        if not from_bytes:
            presence_bytes = word_presence.encode()
            encoded_bytes = struct.pack("I", word_presence.wordID) + struct.pack("I", len(presence_bytes)) +presence_bytes
        else:
            encoded_bytes = word_presence

        if not self.has_space(len(encoded_bytes)):
            raise BarrelFullException()

        # update data file
        with open(self.DATA_FILE_PATH, "ab") as f:
             offset = f.tell()
             f.write(encoded_bytes)

        # update offset file
        with open(self.OFFSET_FILE_PATH, "ab") as f:
            in_barrel_pos = f.tell()/4
            f.write(struct.pack("I", offset)) # 4 bytes per offset

        return int(in_barrel_pos)

    # good luck understanding this :)
    def truncate(self, required_byte_space):

        # complete_encoded_bytes of wordPresences, whose word presences are getting popped
        popped_words = []
        with open(self.DATA_FILE_PATH, "r+b") as data, open(self.OFFSET_FILE_PATH, "r+b") as offsets:

            data.seek(0, io.SEEK_END)
            offsets.seek(0, io.SEEK_END)

            space_created = 0
            end_pos = self.size_bytes()
            while space_created < required_byte_space:

                  # read the offset
                  offsets.seek(-4, io.SEEK_CUR)
                  offset = struct.unpack("I",offsets.read(4))[0]
                  offsets.seek(-4, io.SEEK_CUR) # go back after reading

                  # read the bytes of the next presence and add to popped words
                  data.seek(offset)
                  popped_words.append(data.read(end_pos - offset))

                  space_created += len(popped_words[-1])
                  end_pos = offset



            offsets.truncate(offsets.tell())
            data.seek(-space_created,io.SEEK_END)
            data.truncate(data.tell())

            return popped_words



