import struct


class DocumentBodyWord:
    def __init__(self, wordID, positions):
        self.wordID:int = wordID
        self.positions:list[int] = positions

    def frequency(self):
        return len(self.positions)

class Document:
      def __init__(self, title_words:list[int], tags:list[int], body_words:list[DocumentBodyWord]):
          self.title_words:list[int] = title_words
          self.tags:list[int] = tags
          self.body_words:list[DocumentBodyWord] = body_words # list of DocumentBodyWord

      def word_count(self):
          return len(self.body_words)

      def store(self, index):

          #write data to data file
          bytes = self.encode()
          with open(index.DATA_FILE_PATH, "ab") as fwd_index:
              offset = fwd_index.tell()
              fwd_index.write(bytes)

          # update size counter
          with open(index.DATA_FILE_PATH, "r+b") as fwd_index:
              old_size = struct.unpack("I", fwd_index.read(4))[0]
              fwd_index.seek(0)
              fwd_index.write(struct.pack("I", old_size + 1))

          #write offset to offset file
          with open(index.OFFSET_FILE_PATH, "ab") as offset_file:

                '''
                docIDs are sequential. offset_file is essentially an array of 4 byte integers
                if size (given by tell() in append mode) is 4, it means one document is stored already i.e docID 0
                so next docID will be 4/4 = 1
                '''
                docID = int(offset_file.tell()/4)
                offset_file.write(struct.pack("I", offset)) # offset will be stored as uint32
                return docID

      def encode(self):

          bytes = b''

          #store title words
          num_title_words = len(self.title_words)
          bytes += struct.pack("B", num_title_words) # num_title_words field
          bytes += struct.pack(f"{num_title_words}I", *self.title_words) # title words field

          # store tags
          num_tags = len(self.tags)
          bytes += struct.pack("B", num_tags)  # num_tags field
          bytes += struct.pack(f"{num_tags}I", *self.tags)  # tags words field

          # store DocumentBodyWords
          num_body_words = len(self.body_words)
          bytes += struct.pack("I", num_body_words)  # num_body_words field
          for body_word in self.body_words:
              bytes += struct.pack("I", body_word.wordID) #wordID
              num_positions = len(body_word.positions)
              bytes += struct.pack("H", num_positions)  # num_positions field
              bytes += struct.pack(f"{num_positions}I", *body_word.positions)

          return bytes


