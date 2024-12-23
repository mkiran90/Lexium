import io
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

      def doc_length(self):
          return sum([len(word.positions) for word in self.body_words])

      def store(self, index):

          #write data to data file
          bytes = self.encode()
          with open(index._DATA_FILE_PATH, "ab") as fwd_index:
              offset = fwd_index.tell()

              # write size in bytes in the first 4 bytes
              fwd_index.write(struct.pack("I", len(bytes)))

              fwd_index.write(bytes)

          # update size counter
          with open(index._DATA_FILE_PATH, "r+b") as fwd_index:
              old_size = struct.unpack("I", fwd_index.read(4))[0]
              fwd_index.seek(0)
              fwd_index.write(struct.pack("I", old_size + 1))

          #write offset to offset file
          with open(index._OFFSET_FILE_PATH, "ab") as offset_file:

                '''
                docIDs are sequential. offset_file is essentially an array of 4 byte integers
                if size (given by tell() in append mode) is 4, it means one document is stored already i.e docID 0
                so next docID will be 4/4 = 1
                '''
                docID = int(offset_file.tell()/4)
                offset_file.write(struct.pack("I", offset)) # offset will be stored as uint32
                return docID

      def encode(self):

          bytes = io.BytesIO()

          #store title words
          num_title_words = len(self.title_words)
          bytes.write(struct.pack("B", num_title_words)) # num_title_words field
          bytes.write(struct.pack(f"{num_title_words}I", *self.title_words)) # title words field

          # store tags
          num_tags = len(self.tags)
          bytes.write(struct.pack("B", num_tags))  # num_tags field
          bytes.write(struct.pack(f"{num_tags}I", *self.tags))  # tags words field

          # store DocumentBodyWords
          num_body_words = len(self.body_words)
          bytes.write(struct.pack("I", num_body_words))  # num_body_words field
          for body_word in self.body_words:
              bytes.write(struct.pack("I", body_word.wordID)) #wordID
              num_positions = len(body_word.positions)
              bytes.write(struct.pack("H", num_positions))  # num_positions field
              bytes.write(struct.pack(f"{num_positions}I", *body_word.positions))

          return bytes.getvalue()
      
      @classmethod
      def decode(cls, docbytes:bytes):

          bstream = io.BytesIO(docbytes)

          # Read and decode the number of title words
          num_title_words = struct.unpack("B", bstream.read(1))[0]  # read 1 byte, decode as uint8

          # Read all title word data (4 bytes for each word, decode as uint32)
          title_words_data = bstream.read(num_title_words * 4)
          title_words = list(struct.unpack(f"{num_title_words}I", title_words_data))

          # Read and decode the number of tags
          num_tags = struct.unpack("B", bstream.read(1))[0]  # read 1 byte, decode as uint8

          # Read all tag data (4 bytes for each tag, decode as uint32)
          tags_data = bstream.read(num_tags * 4)
          tags = list(struct.unpack(f"{num_tags}I", tags_data))

          # read DocumentBodyWords
          body_words: list[DocumentBodyWord] = []
          num_body_words = struct.unpack("I", bstream.read(4))[0]
          for _ in range(num_body_words):
              wordID = struct.unpack("I", bstream.read(4))[0]
              num_positions = struct.unpack("H", bstream.read(2))[0]  # 2 byte uint16
              positions = list(struct.unpack(f"{num_positions}I", bstream.read(4 * num_positions)))

              body_words.append(DocumentBodyWord(wordID, positions))

          return Document(title_words, tags, body_words)
        

