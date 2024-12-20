import io
import struct


class WordInDoc:
    def __init__(self, title_positions, body_positions):
        self.title_positions = title_positions
        self.body_positions = body_positions

    def encode(self):
        data = io.BytesIO()

        num_title_pos = len(self.title_positions)
        num_body_pos = len(self.body_positions)

        data.write(struct.pack('B', num_title_pos)) # first byte
        data.write(struct.pack(f'{num_title_pos}B', *(self.title_positions))) # one byte for each pos

        data.write(struct.pack('H', num_body_pos)) # 2 bytes
        data.write(struct.pack(f'{num_body_pos}H', *(self.body_positions)))  # 2 bytes for each pos

        return data.getvalue()

    # we're not storing the number of bytes of each wordPresence so we cant get all the bytes together
    # so we pass it the stream itself, at the appropriate start position,AFTER reading docID (this must be guaranteed by caller)
    @classmethod
    def decode(cls, stream:io.BytesIO):

        num_title_pos = struct.unpack('B',stream.read(1))[0]
        title_positions = list(struct.unpack(f'{num_title_pos}B',stream.read(num_title_pos)))

        num_body_pos = struct.unpack('H', stream.read(2))[0]
        body_positions = list(struct.unpack(f'{num_body_pos}H', stream.read(2*num_body_pos)))

        return WordInDoc(title_positions, body_positions)



# encodes the "presence" of a word in the corpus, which is whats stored against the wordID in inverted index
class WordPresence:
    def __init__(self, wordID):
        self.wordID = wordID
        self.docSet = set()
        self.docMap = {}

    def add_doc(self, docID, wordInDoc: WordInDoc):
        self.docSet.add(docID)
        self.docMap[docID] = wordInDoc

    def encode(self):

        data = io.BytesIO()
        num_wordInDocs = len(self.docSet)
        data.write(struct.pack('I', num_wordInDocs)) # first 4 bytes tell the total number of WordInDocs stored.

        for (docID, wordInDoc) in self.docMap.items():
            data.write(struct.pack('I', docID)) # 4 bytes for docID
            data.write(wordInDoc.encode())


        return data.getvalue()

    @classmethod
    def decode(self, wordID, encoded_bytes):

        stream = io.BytesIO(encoded_bytes)

        word_presence = WordPresence(wordID)

        num_wordInDocs = struct.unpack('I', stream.read(4))[0]

        for _ in range(num_wordInDocs):
            docID = struct.unpack('I', stream.read(4))[0]
            wordInDoc = WordInDoc.decode(stream)
            word_presence.add_doc(docID,  wordInDoc)

        return word_presence





