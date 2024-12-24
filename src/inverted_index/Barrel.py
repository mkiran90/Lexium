import io
import os
import struct
import tempfile
import time

from src.inverted_index.WordPresence import WordPresence

class BarrelFullException(Exception):
    pass

class Barrel:
    _BARREL_CAPACITY = 1024 * 1024 * 1024  # 1GB
    _PARENT_PATH = "../../res/inverted_index/barrels/"

    def __init__(self, barrel_num):

        self.BARREL_PATH = f"{self._PARENT_PATH}{barrel_num}/"
        os.makedirs(self.BARREL_PATH, exist_ok=True)

        self.DATA_FILE_PATH = self.BARREL_PATH + "data.bin"
        self.OFFSET_FILE_PATH = self.BARREL_PATH + "offsets.bin"

        if not os.path.isfile(self.DATA_FILE_PATH):
            open(self.DATA_FILE_PATH, "wb")
        if not os.path.isfile(self.OFFSET_FILE_PATH):
            open(self.OFFSET_FILE_PATH, "wb")

    def has_space(self, num_bytes):
        with open(self.DATA_FILE_PATH, "ab") as f:
            return (self._BARREL_CAPACITY - f.tell()) >= num_bytes

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

    def _get_offset_with_file(self, f, in_barrel_pos):
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
            while chunk := temp_file.read(chunk_size):
                f.write(chunk)

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
            A = time.time()
            self._insert(f, offset + 8 + num_bytes, encoded_bytes)
            print("Insertion: ", time.time() - A)
            # update byte size of wordPresence
            f.seek(offset+4)
            f.write(struct.pack("I", num_bytes + len(encoded_bytes)))

            # update num_docInWords
            f.seek(offset + 8)
            f.write(struct.pack("I", num_docInWords + 1))

            self._increment_offsets(in_barrel_pos, len(encoded_bytes))

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
    # this ensures barrel has required byte space, if barrel already has free required byte space, it wont do anything
    def truncate(self, required_byte_space):

        # complete_encoded_bytes of wordPresences, whose word presences are getting popped
        popped_words = []
        with open(self.DATA_FILE_PATH, "r+b") as data, open(self.OFFSET_FILE_PATH, "r+b") as offsets:

            data.seek(0, io.SEEK_END)


            offsets.seek(0, io.SEEK_END)

            # free space in the barrel before start of truncation.
            free_space = self._BARREL_CAPACITY - data.tell()
            space_created = 0
            end_pos = data.tell()
            while space_created + free_space < required_byte_space:

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
            data.seek(-1 * space_created,io.SEEK_END)
            data.truncate(data.tell())

            return popped_words

    def batch_update_offsets(self, barrel_pos_map, barrel_updates):
        with open(self.OFFSET_FILE_PATH, "r+b") as f:

             num_bytes = 0

             # wordIDs should be sorted by in_barrel_pos
             wordIDs = list(barrel_pos_map.keys())
             for (i,wordID) in enumerate(wordIDs):
                 num_bytes += len(barrel_updates[wordID])
                 start_pos = 4*barrel_pos_map[wordID] + 4 # start from byte AFTER current in_barrel_pos, since a wordID's offset wont change by addition to its own presence
                 f.seek(start_pos)

                 if i!=len(barrel_pos_map)-1:
                     end_pos = 4*barrel_pos_map[wordIDs[i+1]] + 4
                     offset_bytes = f.read(end_pos - start_pos)
                 else:
                     offset_bytes = f.read()

                 f.seek(start_pos) #come back to write again

                 n = len(offset_bytes)//4
                 new_offsets = [(x + num_bytes) for x in struct.unpack(f"{n}I", offset_bytes)]
                 f.write(struct.pack(f"{n}I", *new_offsets))



    def batch_update(self, barrel_pos_map, barrel_updates):

        chunk_size = 256*1024 # 256 KBs

        space_required = sum(len(x) for x in barrel_updates.values())

        # technically should never have to raise
        if not self.has_space(space_required):
            raise BarrelFullException

        with open(self.OFFSET_FILE_PATH, "rb") as offset_file:
            offset_map = {wordID : self._get_offset_with_file(offset_file , pos) for (wordID,pos) in barrel_pos_map.items()}

        with open(self.DATA_FILE_PATH, "r+b") as data, tempfile.NamedTemporaryFile(delete=False) as temp:

            temp_file_path = temp.name
            data.seek(0)

            for wordID in offset_map:
                offset = offset_map[wordID]
                new_bytes = barrel_updates[wordID]
                while data.tell() < offset:
                      temp.write(data.read(min(offset - data.tell(), chunk_size)))
                temp.write(data.read(4)) # skip wordID bytes
                num_bytes = struct.unpack("I",data.read(4))[0]
                temp.write(struct.pack("I", num_bytes + len(new_bytes)))
                num_docInWords = struct.unpack("I", data.read(4))[0]
                temp.write(struct.pack("I", num_docInWords + 1))
                temp.write(new_bytes)

            # copy remaining data
            while chunk:=data.read(chunk_size):
                  temp.write(chunk)

            # Replace the original file content
            data.seek(0)  # Reset file descriptor to the beginning
            temp.seek(0)
            while chunk := temp.read(chunk_size):
                data.write(chunk)

        # Clean up the temporary file
        os.remove(temp_file_path)

        self.batch_update_offsets(barrel_pos_map, barrel_updates)