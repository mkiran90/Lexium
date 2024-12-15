import io
import struct

class DocumentLite:
    def __init__(self, title_words: list[int], tags: list[int], body_words:dict):
        self.title_words: list[int] = title_words
        self.tags: list[int] = tags
        self.body_words: dict = body_words

    def body_word_count(self):
        count = 0
        for word in self.body_words:
            count += len(self.body_words[word])
        return count

    @classmethod
    def decode(cls, docbytes: bytes):

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
        body_words = {}
        num_body_words = struct.unpack("I", bstream.read(4))[0]
        for _ in range(num_body_words):
            wordID = struct.unpack("I", bstream.read(4))[0]
            num_positions = struct.unpack("H", bstream.read(2))[0]  # 2 byte uint16
            positions = list(struct.unpack(f"{num_positions}I", bstream.read(4 * num_positions)))

            body_words[wordID] = positions

        return DocumentLite(title_words, tags, body_words)


